export function formatDateTime(value: string | Date, locales?: Intl.LocalesArgument, options?: Intl.DateTimeFormatOptions) {
  const date = typeof value === 'string' ? new Date(value) : value

  return new Intl.DateTimeFormat(locales, {
    dateStyle: 'medium',
    timeStyle: 'short',
    ...options,
  }).format(date)
}
