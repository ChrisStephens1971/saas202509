/**
 * Converts an array of objects to CSV format and downloads it
 */
export function exportToCsv<T extends Record<string, any>>(
  data: T[],
  filename: string,
  columns: { key: keyof T; header: string }[]
) {
  if (data.length === 0) {
    console.warn('No data to export')
    return
  }

  // Create CSV header
  const headers = columns.map((col) => col.header).join(',')

  // Create CSV rows
  const rows = data.map((item) => {
    return columns
      .map((col) => {
        const value = item[col.key]
        // Handle values that might contain commas or quotes
        if (value === null || value === undefined) {
          return ''
        }
        const stringValue = String(value)
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`
        }
        return stringValue
      })
      .join(',')
  })

  // Combine headers and rows
  const csv = [headers, ...rows].join('\n')

  // Create blob and download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}
