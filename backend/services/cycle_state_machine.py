"""
Cycle State Machine for real-time monitoring
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
import uuid


class CycleState(str, Enum):
    """Cycle states"""
    IDLE = "idle"
    WAITING_START = "waiting_start"
    ACTIVE = "active"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ABORTED = "aborted"


class CycleEvent(str, Enum):
    """Cycle events"""
    REGISTER_STREAM = "register_stream"
    CYCLE_START = "cycle_start"
    CYCLE_STOP = "cycle_stop"
    CYCLE_PAUSE = "cycle_pause"
    CYCLE_RESUME = "cycle_resume"
    SAMPLE_RECEIVED = "sample_received"
    CONNECTION_LOST = "connection_lost"
    TIMEOUT = "timeout"
    MANUAL_ABORT = "manual_abort"


@dataclass
class CycleMetadata:
    """Cycle metadata"""
    cycle_id: str
    stream_id: str
    dataset_id: str
    cycle_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    sample_count: int = 0
    is_reference: bool = False
    health_score: Optional[float] = None
    anomaly_flag: bool = False
    abort_reason: Optional[str] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


class CycleStateMachine:
    """Manages cycle state transitions"""
    
    # Grace period for samples to arrive after stop signal
    GRACE_PERIOD_SEC = 10
    # Timeout for receiving samples
    SAMPLE_TIMEOUT_SEC = 30
    
    def __init__(self, stream_id: str, dataset_id: str):
        self.stream_id = stream_id
        self.dataset_id = dataset_id
        self.state = CycleState.IDLE
        self.current_cycle: Optional[CycleMetadata] = None
        self.cycle_counter = 0
        self.last_sample_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_cycle_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
    
    def transition(self, event: CycleEvent, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Process event and transition state"""
        old_state = self.state
        
        try:
            if event == CycleEvent.REGISTER_STREAM:
                if self.state == CycleState.IDLE:
                    self.state = CycleState.WAITING_START
            
            elif event == CycleEvent.CYCLE_START:
                if self.state in [CycleState.WAITING_START, CycleState.STOPPED, CycleState.ABORTED]:
                    self.state = CycleState.ACTIVE
                    self._start_new_cycle(metadata or {})
            
            elif event == CycleEvent.CYCLE_STOP:
                if self.state == CycleState.ACTIVE:
                    self.state = CycleState.STOPPING
                    self.stop_time = datetime.utcnow()
            
            elif event == CycleEvent.CYCLE_PAUSE:
                if self.state == CycleState.ACTIVE:
                    # Store pause time, but don't change state significantly
                    if self.current_cycle:
                        self.current_cycle.custom_metadata['paused_at'] = datetime.utcnow().isoformat()
            
            elif event == CycleEvent.CYCLE_RESUME:
                if self.state == CycleState.ACTIVE:
                    if self.current_cycle:
                        self.current_cycle.custom_metadata.pop('paused_at', None)
            
            elif event == CycleEvent.SAMPLE_RECEIVED:
                if self.state == CycleState.ACTIVE:
                    self.last_sample_time = datetime.utcnow()
                    if self.current_cycle:
                        self.current_cycle.sample_count += 1
                
                elif self.state == CycleState.STOPPING:
                    # Still receiving samples in grace period
                    self.last_sample_time = datetime.utcnow()
                    if self.current_cycle:
                        self.current_cycle.sample_count += 1
                    
                    # Check grace period elapsed
                    if self._grace_period_elapsed():
                        self.state = CycleState.STOPPED
                        self._complete_cycle()
            
            elif event == CycleEvent.TIMEOUT:
                if self.state == CycleState.ACTIVE:
                    # Connection loss - abort
                    self.state = CycleState.ABORTED
                    if self.current_cycle:
                        self.current_cycle.abort_reason = "sample_timeout"
                    self._complete_cycle()
                
                elif self.state == CycleState.STOPPING:
                    # Grace period timeout - finalize
                    if self._grace_period_elapsed():
                        self.state = CycleState.STOPPED
                        self._complete_cycle()
            
            elif event == CycleEvent.CONNECTION_LOST:
                if self.state in [CycleState.ACTIVE, CycleState.STOPPING]:
                    self.state = CycleState.ABORTED
                    if self.current_cycle:
                        self.current_cycle.abort_reason = "connection_lost"
                    self._complete_cycle()
            
            elif event == CycleEvent.MANUAL_ABORT:
                if self.state in [CycleState.ACTIVE, CycleState.STOPPING]:
                    self.state = CycleState.ABORTED
                    if self.current_cycle:
                        self.current_cycle.abort_reason = "manual_abort"
                    self._complete_cycle()
            
            # Notify on state change
            if old_state != self.state and self.on_state_change:
                self.on_state_change(
                    stream_id=self.stream_id,
                    old_state=old_state,
                    new_state=self.state,
                    cycle_id=self.current_cycle.cycle_id if self.current_cycle else None
                )
            
            return True
        
        except Exception as e:
            if self.on_error:
                self.on_error(f"State transition error: {e}")
            return False
    
    def _start_new_cycle(self, metadata: Dict[str, Any]) -> None:
        """Start a new cycle"""
        self.cycle_counter += 1
        self.current_cycle = CycleMetadata(
            cycle_id=str(uuid.uuid4()),
            stream_id=self.stream_id,
            dataset_id=self.dataset_id,
            cycle_number=self.cycle_counter,
            start_time=datetime.utcnow(),
            custom_metadata=metadata
        )
        self.last_sample_time = datetime.utcnow()
    
    def _grace_period_elapsed(self) -> bool:
        """Check if grace period has elapsed since stop"""
        if not self.stop_time:
            return False
        
        elapsed = (datetime.utcnow() - self.stop_time).total_seconds()
        return elapsed >= self.GRACE_PERIOD_SEC
    
    def _complete_cycle(self) -> None:
        """Mark cycle as complete"""
        if self.current_cycle:
            self.current_cycle.end_time = datetime.utcnow()
            
            if self.on_cycle_complete:
                self.on_cycle_complete(self.current_cycle)
    
    def check_sample_timeout(self) -> None:
        """Periodically check for sample timeout"""
        if self.state == CycleState.ACTIVE and self.last_sample_time:
            elapsed = (datetime.utcnow() - self.last_sample_time).total_seconds()
            if elapsed > self.SAMPLE_TIMEOUT_SEC:
                self.transition(CycleEvent.TIMEOUT)
        
        elif self.state == CycleState.STOPPING:
            if self._grace_period_elapsed():
                self.transition(CycleEvent.TIMEOUT)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current state status"""
        return {
            "stream_id": self.stream_id,
            "state": self.state.value,
            "cycle_id": self.current_cycle.cycle_id if self.current_cycle else None,
            "cycle_number": self.current_cycle.cycle_number if self.current_cycle else None,
            "start_time": self.current_cycle.start_time.isoformat() if self.current_cycle else None,
            "sample_count": self.current_cycle.sample_count if self.current_cycle else 0,
            "last_sample_time": self.last_sample_time.isoformat() if self.last_sample_time else None,
        }


# Example usage
if __name__ == "__main__":
    fsm = CycleStateMachine("stream-1", "dataset-1")
    
    def on_state_change(**kwargs):
        print(f"🔄 State change: {kwargs['old_state']} → {kwargs['new_state']}")
    
    def on_cycle_complete(cycle):
        print(f"✅ Cycle {cycle.cycle_id} complete: {cycle.sample_count} samples")
    
    fsm.on_state_change = on_state_change
    fsm.on_cycle_complete = on_cycle_complete
    
    # Simulate cycle
    print("📝 Registering stream...")
    fsm.transition(CycleEvent.REGISTER_STREAM)
    
    print("▶️  Starting cycle...")
    fsm.transition(CycleEvent.CYCLE_START, {"test": "metadata"})
    
    print("📊 Receiving samples...")
    for i in range(5):
        fsm.transition(CycleEvent.SAMPLE_RECEIVED)
    
    print("⏹️  Stopping cycle...")
    fsm.transition(CycleEvent.CYCLE_STOP)
    
    print("📊 Grace period - still receiving samples...")
    for i in range(3):
        fsm.transition(CycleEvent.SAMPLE_RECEIVED)
    
    # Simulate grace period elapsed
    import time
    fsm.stop_time = datetime.utcnow() - timedelta(seconds=11)
    fsm.transition(CycleEvent.SAMPLE_RECEIVED)
    
    print(f"\n📈 Status: {fsm.get_status()}")
