import type { Metadata } from 'next'
import { Providers } from '@/components/providers'
import './globals.css'

// Remove Inter font import temporarily until we fix the font issue

export const metadata: Metadata = {
  title: 'School Management System',
  description: 'A comprehensive school management system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}