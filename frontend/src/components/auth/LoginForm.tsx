'use client';

import React, { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/use-toast';
import apiClient from '@/lib/api';

const formSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

export function LoginForm() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  


  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  // Form submission handler
  const [error, setError] = useState<string | null>(null);
  
  const onSubmit = useCallback(async (data: z.infer<typeof formSchema>) => {
    try {
      setError(null);
      setIsLoading(true);
      const loginData = {
        username: data.username,
        password: data.password
      };

      // Call login API
      const response = await apiClient.login(loginData);
      
      if (response?.data?.access_token) {
        // Store auth data
        localStorage.setItem('token', response.data.access_token);
        if (response.data.user) {
          localStorage.setItem('user', JSON.stringify(response.data.user));
        }
        
        // Show success message
        toast({
          title: 'Success',
          description: 'Logged in successfully',
        });
        
        // Redirect to dashboard
        router.push('/dashboard');
      }
    } catch (error: any) {
      // Handle error
      const errorMessage = error?.response?.data?.detail || 'Invalid credentials';
      setError(errorMessage);
      
      // Show error toast
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  return (
    <Form {...form}>
      <form 
        data-testid="login-form" 
        role="form" 
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-4">
        {error && (
          <div role="alert" className="text-red-500">
            {error}
          </div>
        )}
        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="Enter your username" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <Input type="password" placeholder="Enter your password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </Button>
      </form>
    </Form>
  );
}
