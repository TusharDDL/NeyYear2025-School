'use client';

import { useState, useCallback } from 'react';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from '@/components/ui/use-toast';
import apiClient from '@/lib/api';

const formSchema = z.object({
  email: z.string().email('Invalid email address'),
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  role: z.enum(['student', 'teacher', 'parent', 'librarian']),
});

export function RegisterForm() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: '',
      username: '',
      password: '',
      first_name: '',
      last_name: '',
      role: 'student', // Default role for registration
    },
  });

  const [error, setError] = useState<string | null>(null);

  const onSubmit = useCallback(async (data: z.infer<typeof formSchema>) => {
    try {
      console.log('Form submission started with data:', data);
      console.log('Form validation state:', form.formState);
      console.log('Form errors:', form.formState.errors);
      console.log('Form is valid:', form.formState.isValid);
      console.log('Form is submitting:', form.formState.isSubmitting);
      console.log('Form is submitted:', form.formState.isSubmitted);
      
      setError(null);
      setIsLoading(true);
      
      const registerData = {
        email: data.email.trim(),
        username: data.username.trim(),
        password: data.password,
        first_name: data.first_name.trim(),
        last_name: data.last_name.trim(),
        role: data.role
      };
      
      console.log('Attempting to register with data:', registerData);
      const response = await apiClient.register(registerData);
      console.log('Registration API response:', response);
      
      if (response?.data) {
        toast({
          title: 'Success',
          description: 'Registration successful. Please login.',
        });
        router.push('/login');
      } else {
        throw new Error('Registration failed: No response data');
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      const errorMessage = error?.response?.data?.detail || error.message || 'Registration failed';
      setError(errorMessage);
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
      return Promise.reject(error); // Properly reject the promise for tests
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  return (
    <Form {...form}>
      {error && (
        <div role="alert" className="text-red-500 mb-4">
          {error}
        </div>
      )}
      <form 
        data-testid="register-form" 
        role="form" 
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-4">
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="Enter your email" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="Choose a username" {...field} />
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
                <Input type="password" placeholder="Choose a password" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="first_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>First Name</FormLabel>
              <FormControl>
                <Input placeholder="Enter your first name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="last_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Last Name</FormLabel>
              <FormControl>
                <Input placeholder="Enter your last name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="role"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Role</FormLabel>
              <Select 
                onValueChange={field.onChange} 
                value={field.value}
                defaultValue="student"
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select your role" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="student" role="option" data-testid="role-student">Student</SelectItem>
                  <SelectItem value="teacher" role="option" data-testid="role-teacher">Teacher</SelectItem>
                  <SelectItem value="parent" role="option" data-testid="role-parent">Parent</SelectItem>
                  <SelectItem value="librarian" role="option" data-testid="role-librarian">Librarian</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? 'Registering...' : 'Register'}
        </Button>
      </form>
    </Form>
  );
}
