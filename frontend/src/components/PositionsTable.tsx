import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
} from '@mui/material';
import { Position } from '../types';

interface PositionsTableProps {
  positions: Position[];
}

const PositionsTable: React.FC<PositionsTableProps> = ({ positions }) => {
  if (positions.length === 0) {
    return <Typography>No open positions.</Typography>;
  }

  const formatPnl = (pnl: number) => (
    <Typography color={pnl >= 0 ? 'success.main' : 'error.main'}>
      {pnl.toFixed(4)}
    </Typography>
  );

  return (
    <TableContainer component={Paper}>
      <Table sx={{ minWidth: 650 }} aria-label="positions table">
        <TableHead>
          <TableRow>
            <TableCell>Coin</TableCell>
            <TableCell>Type</TableCell>
            <TableCell align="right">Size</TableCell>
            <TableCell align="right">Entry Price</TableCell>
            <TableCell align="right">Position Value</TableCell>
            <TableCell align="right">Unrealized PNL</TableCell>
            <TableCell align="right">Leverage</TableCell>
            <TableCell align="right">Liq. Price</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {positions.map((pos) => (
            <TableRow key={`${pos.coin}-${pos.type}`}>
              <TableCell component="th" scope="row">
                {pos.coin}
              </TableCell>
              <TableCell>
                <Chip
                  label={pos.type}
                  size="small"
                  color={pos.type === 'perp' ? 'primary' : 'secondary'}
                />
              </TableCell>
              <TableCell align="right">{pos.size.toFixed(4)}</TableCell>
              <TableCell align="right">
                {pos.entry_price ? `$${pos.entry_price.toFixed(4)}` : 'N/A'}
              </TableCell>
              <TableCell align="right">
                {pos.position_value ? `$${pos.position_value.toFixed(2)}` : 'N/A'}
              </TableCell>
              <TableCell align="right">
                {pos.unrealized_pnl ? formatPnl(pos.unrealized_pnl) : 'N/A'}
              </TableCell>
              <TableCell align="right">{pos.leverage ? `${pos.leverage.toFixed(2)}x` : 'N/A'}</TableCell>
              <TableCell align="right">
                {pos.liquidation_price ? `$${pos.liquidation_price.toFixed(2)}` : 'N/A'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default PositionsTable;
