"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateStudent } from "@/lib/hooks";

const formSchema = z.object({
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  admission_number: z.string().min(1, "Admission number is required"),
  roll_number: z.string().min(1, "Roll number is required"),
  class_name: z.string().min(1, "Class is required"),
  section: z.string().min(1, "Section is required"),
  date_of_birth: z.string().min(1, "Date of birth is required"),
  gender: z.enum(["male", "female", "other"]),
  blood_group: z.string().optional(),
  address: z.string().optional(),
  phone: z.string().optional(),
  parent_name: z.string().min(1, "Parent name is required"),
  parent_phone: z.string().min(1, "Parent phone is required"),
  parent_email: z.string().email("Invalid email address"),
  emergency_contact: z.string().optional(),
  medical_conditions: z.string().optional(),
});

export function StudentForm() {
  const router = useRouter();
  const { mutate: createStudent, isLoading } = useCreateStudent();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      admission_number: "",
      roll_number: "",
      class_name: "",
      section: "",
      date_of_birth: "",
      gender: "male",
      parent_name: "",
      parent_phone: "",
      parent_email: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    createStudent(values, {
      onSuccess: () => {
        router.push("/students");
      },
    });
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-4"
        role="form"
        data-testid="student-form"
      >
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="first_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>First Name</FormLabel>
                <FormControl>
                  <Input {...field} />
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
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="admission_number"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Admission Number</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="roll_number"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Roll Number</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="class_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel id="class-label">Class</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger
                      data-testid="class-select"
                      aria-label="Class"
                      aria-labelledby="class-label"
                    >
                      <SelectValue placeholder="Select class" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {Array.from({ length: 10 }, (_, i) => (
                      <SelectItem
                        key={i + 1}
                        value={`Class ${i + 1}`}
                        role="option"
                      >
                        Class {i + 1}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="section"
            render={({ field }) => (
              <FormItem>
                <FormLabel id="section-label">Section</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger
                      data-testid="section-select"
                      aria-label="Section"
                      aria-labelledby="section-label"
                    >
                      <SelectValue placeholder="Select section" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {["A", "B", "C"].map((section) => (
                      <SelectItem key={section} value={section} role="option">
                        Section {section}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="date_of_birth"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Date of Birth</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="gender"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Gender</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="male">Male</SelectItem>
                    <SelectItem value="female">Female</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="parent_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Parent Name</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="parent_phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Parent Phone</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="parent_email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Parent Email</FormLabel>
                <FormControl>
                  <Input type="email" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="emergency_contact"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Emergency Contact</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="address"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Address</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="medical_conditions"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Medical Conditions</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Saving..." : "Save Student"}
        </Button>
      </form>
    </Form>
  );
}
