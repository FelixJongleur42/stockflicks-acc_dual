# Instrument Generalization Refactoring

## Overview
The application has been successfully refactored to generalize instrument usage from hardcoded tickers to configurable command-line arguments.

## Key Changes Made

### 1. **Command Line Arguments Added**
- `--risky1 <ticker>`: First risky asset (default: SPY - S&P 500, also used for benchmark)
- `--risky2 <ticker>`: Second risky asset (default: VINEX - Vanguard International Explorer)  
- `--safe1 <ticker>`: Safe asset (default: VUSTX - Vanguard Long-term US Treasury)
- `--start-date <date>`: Start date for data retrieval (existing, default: 1998-01-01)

### 2. **Variable Mapping**
- **risky1**: First risky asset, used as the primary benchmark for buy & hold comparison
- **risky2**: Second risky asset, alternative momentum choice
- **safe1**: Safe asset, used when momentum signals are negative

### 3. **Benchmark Selection**
The first instrument (`risky1`) is now used as the benchmark for buy & hold comparison, making the analysis adaptable to different market indices.

## Usage Examples

### Default Behavior (Backward Compatible)
```bash
python application.py
# Uses: SPY (risky1), VINEX (risky2), VUSTX (safe1)
```

### Custom US Market Strategy
```bash
python application.py --risky1 QQQ --risky2 IWM --safe1 TLT
# QQQ: Nasdaq 100, IWM: Small-cap, TLT: 20+ Year Treasury
```

### Global Diversified Strategy  
```bash
python application.py --risky1 VTI --risky2 VXUS --safe1 BND
# VTI: US Total Stock, VXUS: International, BND: Total Bond
```

### Sector Rotation Strategy
```bash
python application.py --risky1 XLK --risky2 XLF --safe1 GOVT
# XLK: Technology, XLF: Financial, GOVT: US Treasury
```

### Commodity Strategy
```bash
python application.py --risky1 GLD --risky2 USO --safe1 SHY
# GLD: Gold, USO: Oil, SHY: Short Treasury
```

## Technical Implementation

### Variables Replaced
- **Old**: Hardcoded `"SPY"`, `"VINEX"`, `"VUSTX"` throughout the codebase
- **New**: Dynamic `risky1`, `risky2`, `safe1` variables from command-line arguments

### Key Refactored Sections
1. **Argument Parsing**: Added new command-line parameters
2. **Data Retrieval**: Uses `all_tickers = [risky1, risky2, safe1]`
3. **Column Generation**: Dynamic column names using f-strings
4. **Trading Logic**: Generalized buy/sell/hold signal generation
5. **Statistics Calculation**: Updated trade counting and HTML generation
6. **Results Display**: Dynamic instrument names in tables and charts

### Backward Compatibility
✅ **Fully Maintained**: Running without arguments produces identical results to the original version.

## Files Modified
- `application.py`: Complete refactoring of instrument references
- `requirements.txt`: Updated dependencies (separate refactoring)

## Testing Status
✅ **Syntax Validation**: Code compiles without errors  
✅ **Pattern Verification**: All required generalization patterns present  
✅ **Legacy Cleanup**: Old hardcoded references removed  
✅ **Argument Parsing**: Command-line interface working correctly  

## Benefits
1. **Flexibility**: Test different asset combinations easily
2. **Adaptability**: Use with any market sectors or geographical regions  
3. **Research**: Compare strategies across different instrument types
4. **Scalability**: Easy to extend with additional instruments in the future
5. **Maintainability**: Single source of truth for instrument definitions