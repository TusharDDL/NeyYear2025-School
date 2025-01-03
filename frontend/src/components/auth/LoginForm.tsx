'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/components/ui/use-toast'

interface LoginResponse {
  access: string
  refresh: string
  user_id: number
  username: string
  email: string
  role: string
  school_id: number | null
}

export default function LoginForm() {
  const router = useRouter()
  const { toast } = useToast()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const loginMutation = useMutation({
    mutationFn: async (credentials: { username: string; password: string }) => {
      try {
        console.log('Starting login request...')
        const response = await fetch('/api/v1/accounts/token/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-School-Domain': window.location.hostname
          },
          credentials: 'include',
          body: JSON.stringify(credentials)
        })

        console.log('Response status:', response.status)
        
        const contentType = response.headers.get('content-type')
        if (!contentType || !contentType.includes('application/json')) {
          throw new Error('Invalid response from server')
        }

        const data = await response.json()
        console.log('Response data received:', data)

        if (!response.ok) {
          throw new Error(data.detail || 'Login failed')
        }

        return data as LoginResponse
      } catch (error) {
        console.error('Login error:', error)
        throw error
      }
    },
    onSuccess: (data) => {
      console.log('Processing successful login...')
      
      // Store the tokens
      document.cookie = `accessToken=${data.access}; path=/`
      document.cookie = `refreshToken=${data.refresh}; path=/`
      
      // Store user data in cookies
      const userData = {
        id: data.user_id,
        username: data.username,
        email: data.email,
        role: data.role,
        school_id: data.school_id
      }
      document.cookie = `userData=${JSON.stringify(userData)}; path=/`

      // Show success message
      toast({
        title: 'Login successful',
        description: `Welcome back, ${data.username}!`,
      })

      // Navigate after successful login
      console.log('Navigating to dashboard...')
      
      // Use a small delay to ensure state updates are complete
      setTimeout(() => {
        // Try multiple navigation methods
        try {
          router.push('/dashboard')
          router.refresh()
        } catch (error) {
          console.error('Navigation error:', error)
          // Fallback to window.location if router fails
          window.location.href = '/dashboard'
        }
      }, 100)
    },
    onError: (error: Error) => {
      console.error('Login error:', error)
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message || 'An error occurred during login'
      })
    }
  })

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    console.log('Form submitted')
    loginMutation.mutate({ username, password })
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl text-center">School Management System</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {loginMutation.error instanceof Error && (
            <Alert variant="destructive">
              <AlertDescription>{loginMutation.error.message}</AlertDescription>
            </Alert>
          )}
          
          <div className="space-y-2">
            <label htmlFor="username" className="text-sm font-medium">
              Username
            </label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="Enter your username"
              className="w-full"
              autoComplete="username"
              disabled={loginMutation.isPending}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
              className="w-full"
              autoComplete="current-password"
              disabled={loginMutation.isPending}
            />
          </div>

          <Button 
            type="submit" 
            className="w-full"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? 'Signing in...' : 'Sign In'}
          </Button>

          <div className="text-center text-sm text-gray-500 mt-4">
            <a href="/forgot-password" className="text-blue-500 hover:text-blue-600">
              Forgot password?
            </a>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
