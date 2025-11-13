# Timeline Chart Feature Documentation

## Overview
This document describes the timeline chart feature that shows which instrument was being held by the dual momentum strategy at each point in time with color coding.

## Feature Description
The timeline chart provides a visual representation of instrument allocation over time, showing:
- **Which instrument was held**: SPY, VINEX, or VUSTX (or user-defined alternatives)
- **Duration of each holding period**: How long each instrument was held
- **Color coding**: Each instrument has a distinct color for easy identification
- **Interactive tooltips**: Hover over segments to see detailed information

## Visual Design

### Color Scheme
- **Risky Asset 1 (SPY)**: Blue (#3498db) - Primary risky asset and benchmark
- **Risky Asset 2 (VINEX)**: Red (#e74c3c) - Secondary risky asset  
- **Safe Asset (VUSTX)**: Green (#2ecc71) - Safe haven asset

### Layout
- **Timeline Bar**: Horizontal bar showing time progression from left to right
- **Segments**: Colored segments representing holding periods for each instrument
- **Legend**: Below the timeline showing color mappings to instruments
- **Axis**: Time markers showing start, middle, and end years
- **Tooltips**: Interactive hover information with dates and duration

## Technical Implementation

### Data Processing
1. **Extract Holdings**: Parse `results["Output"]` column to identify instrument switches
2. **Create Segments**: Group consecutive periods of the same instrument
3. **Calculate Positioning**: Convert time periods to percentage positions
4. **Generate JSON**: Serialize timeline data for JavaScript consumption

### Frontend Components
1. **HTML Structure**: Container with timeline chart div and legend
2. **CSS Styling**: Responsive design with hover effects and tooltips
3. **JavaScript Logic**: Dynamic segment creation and interactivity
4. **Positioning**: Calculate relative widths and positions based on time periods

## User Interaction

### Hover Effects
- Segments expand slightly on hover for better visibility
- Detailed tooltip appears showing:
  - Instrument name
  - Start and end dates
  - Duration in months
- Smooth transitions and animations

### Responsive Design
- Adapts to different screen sizes
- Legend wraps on smaller screens
- Tooltip positioning adjusts to viewport

## Integration with Existing Features

### Command Line Arguments
- Timeline automatically uses the configured instrument names (--risky1, --risky2, --safe1)
- Colors and labels update based on user-specified tickers

### Data Consistency
- Timeline data is synchronized with the main results data
- Reflects the same investment decisions shown in tables and performance chart
- Updates automatically when parameters change

## Code Structure

### New Functions Added
```python
def generate_timeline_data():
    """Generate data for instrument timeline chart"""
    # Processes results["Output"] to create timeline segments
    # Returns JSON data for JavaScript consumption
```

### CSS Classes Added
- `.timeline-container`: Main container styling
- `.timeline-chart`: Chart area with positioning
- `.timeline-segment`: Individual instrument holding periods
- `.timeline-legend`: Color legend display
- `.timeline-tooltip`: Interactive hover information

### JavaScript Components
- Timeline segment creation and positioning
- Hover event handling for tooltips
- Axis and label generation
- Responsive tooltip positioning

## Performance Considerations

### Optimization Features
- Segments only display instrument names if they're wide enough
- Efficient DOM manipulation for timeline creation
- Smooth CSS transitions without impacting performance
- Tooltip positioning cached during mouse movement

### Data Sampling
- Timeline uses full resolution data for accuracy
- Visual segments automatically adjust based on data density
- Handles both short and long investment periods effectively

## Usage Examples

### Standard Configuration
```bash
python application.py
# Shows timeline with SPY (blue), VINEX (red), VUSTX (green)
```

### Custom Instruments
```bash
python application.py --risky1 QQQ --risky2 EFA --safe1 TLT
# Timeline automatically updates colors and labels for QQQ, EFA, TLT
```

## Future Enhancements

### Potential Improvements
1. **Zoom Functionality**: Allow users to zoom into specific time periods
2. **Multiple Strategies**: Compare timelines of different strategy configurations
3. **Performance Overlay**: Show performance metrics within timeline segments
4. **Export Options**: Allow timeline export as image or PDF

### Data Enhancements
1. **Transition Markers**: Highlight specific dates when switches occurred
2. **Volume Information**: Show relative investment amounts in segments
3. **Benchmark Comparison**: Side-by-side timeline with buy-and-hold strategy

## Troubleshooting

### Common Issues
1. **Missing Segments**: Check if results["Output"] contains valid data
2. **Tooltip Positioning**: Ensure proper CSS z-index and positioning
3. **Color Conflicts**: Verify instrument color mappings in generate_timeline_data()

### Debugging Tips
1. Check browser console for JavaScript errors
2. Verify timeline data JSON structure in network tab
3. Ensure CSS styles are loading correctly
4. Test with different data ranges and instruments

## Implementation History
- **Added**: November 13, 2025
- **Purpose**: Visual representation of instrument allocation over time
- **Integration**: Seamlessly integrated with existing dual momentum application
- **Testing**: Validated with syntax checking and feature testing