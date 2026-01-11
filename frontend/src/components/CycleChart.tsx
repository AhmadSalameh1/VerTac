import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import { SensorData } from '../services/api';
import './CycleChart.css';

interface CycleChartProps {
  sensorData: SensorData[];
}

const CycleChart: React.FC<CycleChartProps> = ({ sensorData }) => {
  const [selectedSensors, setSelectedSensors] = useState<string[]>(
    sensorData.slice(0, 3).map((s) => s.sensor_name)
  );

  const toggleSensor = (sensorName: string) => {
    setSelectedSensors((prev) =>
      prev.includes(sensorName)
        ? prev.filter((s) => s !== sensorName)
        : [...prev, sensorName]
    );
  };

  const traces = sensorData
    .filter((sensor) => selectedSensors.includes(sensor.sensor_name))
    .map((sensor) => ({
      x: sensor.timestamps,
      y: sensor.values,
      type: 'scatter' as const,
      mode: 'lines' as const,
      name: sensor.sensor_name,
      line: {
        width: 2,
      },
    }));

  return (
    <div className="cycle-chart">
      <div className="sensor-selector">
        <label>Select Sensors:</label>
        <div className="sensor-chips">
          {sensorData.map((sensor) => (
            <button
              key={sensor.sensor_name}
              className={`sensor-chip ${
                selectedSensors.includes(sensor.sensor_name) ? 'active' : ''
              }`}
              onClick={() => toggleSensor(sensor.sensor_name)}
            >
              {sensor.sensor_name}
            </button>
          ))}
        </div>
      </div>

      {traces.length > 0 ? (
        <Plot
          data={traces}
          layout={{
            title: 'Sensor Time Series',
            xaxis: {
              title: 'Time',
              gridcolor: '#e5e7eb',
            },
            yaxis: {
              title: 'Value',
              gridcolor: '#e5e7eb',
            },
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff',
            autosize: true,
            margin: {
              l: 60,
              r: 40,
              t: 60,
              b: 60,
            },
            hovermode: 'x unified',
            legend: {
              orientation: 'h' as const,
              y: -0.2,
            },
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          }}
          style={{ width: '100%', height: '500px' }}
        />
      ) : (
        <div className="no-sensors-selected">
          <p>Select at least one sensor to display</p>
        </div>
      )}
    </div>
  );
};

export default CycleChart;
