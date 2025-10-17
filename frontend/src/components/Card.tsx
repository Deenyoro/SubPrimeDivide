interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
}

export default function Card({ children, className = '', hover = false }: CardProps) {
  return (
    <div
      className={`bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6 border border-gray-200 dark:border-gray-700 ${
        hover ? 'transition-shadow hover:shadow-xl' : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}
