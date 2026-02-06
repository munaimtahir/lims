export function calculateAgeFromDob(dobString: string, today = new Date()): { years: number; months: number; days: number } | null {
  if (!dobString) return null;
  const dob = new Date(`${dobString}T00:00:00`);
  if (Number.isNaN(dob.getTime())) return null;

  let years = today.getFullYear() - dob.getFullYear();
  let months = today.getMonth() - dob.getMonth();
  let days = today.getDate() - dob.getDate();

  if (days < 0) {
    const prevMonth = new Date(today.getFullYear(), today.getMonth(), 0);
    days += prevMonth.getDate();
    months -= 1;
  }

  if (months < 0) {
    months += 12;
    years -= 1;
  }

  return { years, months, days };
}

export function calculateDobFromAge(
  years: number,
  months = 0,
  days = 0,
  today = new Date(),
): string | null {
  if (Number.isNaN(years) || years < 0) return null;

  let year = today.getFullYear() - years;
  let month = today.getMonth() + 1 - months;

  while (month <= 0) {
    month += 12;
    year -= 1;
  }

  // Calculate the target day, accounting for the days parameter
  const targetDay = today.getDate() - days;
  const maxDayInMonth = new Date(year, month, 0).getDate();
  const day = Math.min(Math.max(1, targetDay), maxDayInMonth);
  const dob = new Date(year, month - 1, day);

  // Return local date string YYYY-MM-DD
  const y = dob.getFullYear();
  const m = String(dob.getMonth() + 1).padStart(2, '0');
  const d = String(dob.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}
