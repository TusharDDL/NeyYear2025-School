'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated, getUserData } from '@/lib/auth-utils'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'
import {
  BookOpen,
  ClipboardList,
  UserCheck,
  GraduationCap,
  CreditCard,
  Bell,
} from 'lucide-react'

interface DashboardCard {
  title: string
  description: string
  icon: React.ReactNode
  bgColor: string
  textColor: string
  iconColor: string
}

const dashboardCards: DashboardCard[] = [
  {
    title: 'Classes',
    description: 'View your class schedule and materials',
    icon: <BookOpen size={24} />,
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
    iconColor: 'text-blue-600',
  },
  {
    title: 'Assignments',
    description: 'Check your pending assignments',
    icon: <ClipboardList size={24} />,
    bgColor: 'bg-green-50',
    textColor: 'text-green-700',
    iconColor: 'text-green-600',
  },
  {
    title: 'Attendance',
    description: 'View your attendance records',
    icon: <UserCheck size={24} />,
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-700',
    iconColor: 'text-purple-600',
  },
  {
    title: 'Grades',
    description: 'Check your academic performance',
    icon: <GraduationCap size={24} />,
    bgColor: 'bg-yellow-50',
    textColor: 'text-yellow-700',
    iconColor: 'text-yellow-600',
  },
  {
    title: 'Fees',
    description: 'View and pay your fees',
    icon: <CreditCard size={24} />,
    bgColor: 'bg-red-50',
    textColor: 'text-red-700',
    iconColor: 'text-red-600',
  },
  {
    title: 'Announcements',
    description: 'Stay updated with school news',
    icon: <Bell size={24} />,
    bgColor: 'bg-indigo-50',
    textColor: 'text-indigo-700',
    iconColor: 'text-indigo-600',
  },
]

interface UserData {
  id: number
  username: string
  email: string
  role: string
  school_id: number | null
}

export default function DashboardPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [userData, setUserData] = useState<UserData | null>(null)

  useEffect(() => {
    const checkAuth = () => {
      console.log('Checking authentication status...')
      
      if (!isAuthenticated()) {
        console.log('Not authenticated, redirecting to login')
        router.push('/login')
        return
      }

      const user = getUserData()
      if (!user) {
        console.log('No user data found, redirecting to login')
        router.push('/login')
        return
      }

      console.log('User authenticated:', user)
      setUserData(user)
      setIsLoading(false)
    }

    checkAuth()
  }, [router])

  const handleCardClick = (title: string) => {
    toast({
      title: 'Coming Soon',
      description: `${title} feature will be available soon!`,
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!userData) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Welcome, {userData.username}!
              </h1>
              <p className="text-gray-600 mt-1">
                Role: {userData.role.replace('_', ' ').toUpperCase()}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => {
                localStorage.clear()
                router.push('/login')
              }}
            >
              Logout
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dashboardCards.map((card, index) => (
            <button
              key={index}
              onClick={() => handleCardClick(card.title)}
              className={`${
                card.bgColor
              } p-6 rounded-lg shadow-sm transition-transform duration-200 hover:scale-105 text-left w-full ${
                isLoading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              disabled={isLoading}
            >
              <div className="flex items-center mb-4">
                <div className={`${card.iconColor} mr-3`}>{card.icon}</div>
                <h2 className={`text-lg font-semibold ${card.textColor}`}>
                  {card.title}
                </h2>
              </div>
              <p className={`${card.iconColor}`}>{card.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}