export function normalizeDateInputToISO(value: string): string {
  const input = value.trim();
  if (!input) return '';

  if (/^\d{4}-\d{2}-\d{2}$/.test(input)) return input;
  if (/^\d{4}-\d{2}-\d{2}T/.test(input)) return input.slice(0, 10);

  const slashParts = input.split('/');
  if (slashParts.length === 3) {
    let [first, second, third] = slashParts.map((p) => Number(p));
    if ([first, second, third].some(Number.isNaN)) return '';

    // Prefer DD/MM format. If impossible, fallback to MM/DD normalization.
    let day = first;
    let month = second;
    let year = third;

    if (first <= 12 && second > 12) {
      month = first;
      day = second;
    }

    if (third < 100) {
      year = third >= 70 ? 1900 + third : 2000 + third;
    }

    if (month < 1 || month > 12 || day < 1 || day > 31) return '';

    return `${year.toString().padStart(4, '0')}-${month
      .toString()
      .padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
  }

  return '';
}

export function formatDateDDMMYY(value?: string | null): string {
  if (!value) return '';
  const iso = normalizeDateInputToISO(value);
  if (!iso) return '';
  const [year, month, day] = iso.split('-');
  return `${day}/${month}/${year.slice(-2)}`;
}
