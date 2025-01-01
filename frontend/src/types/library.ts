export interface Book {
  id: number
  title: string
  author: string
  isbn: string
  quantity: number
  available: number
  category?: string
  description?: string
  published_year?: number
}
