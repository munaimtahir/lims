export function formatCurrency(amount: string | number, currency: string) {
  const value = typeof amount === 'number' ? amount.toFixed(2) : amount;
  return `${currency} ${value}`;
}
