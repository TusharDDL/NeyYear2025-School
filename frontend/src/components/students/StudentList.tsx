"use client";

import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useStudents } from "@/lib/hooks";
import { Student } from "@/lib/types";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

export function StudentList() {
  const [filters, setFilters] = useState({
    class_name: "",
    section: "",
    search: "",
  });

  const { data: students, isLoading } = useStudents({
    class_name: filters.class_name,
    section: filters.section,
    search: filters.search,
  });

  const handleSearch = (value: string) => {
    setFilters((prev) => ({ ...prev, search: value }));
  };

  const handleClassChange = (value: string) => {
    setFilters((prev) => ({ ...prev, class_name: value }));
  };

  const handleSectionChange = (value: string) => {
    setFilters((prev) => ({ ...prev, section: value }));
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Input
          placeholder="Search students..."
          value={filters.search}
          onChange={(e) => handleSearch(e.target.value)}
          className="max-w-sm"
        />
        <Select value={filters.class_name} onValueChange={handleClassChange}>
          <SelectTrigger
            data-testid="class-select"
            className="w-[180px]"
            aria-label="Class"
            aria-labelledby="class-label"
          >
            <SelectValue placeholder="Select class" />
          </SelectTrigger>
          <SelectContent data-testid="class-content">
            <SelectItem
              data-testid="class-option-1"
              value="Class 1"
              role="option"
            >
              Class 1
            </SelectItem>
            <SelectItem
              data-testid="class-option-2"
              value="Class 2"
              role="option"
            >
              Class 2
            </SelectItem>
            <SelectItem
              data-testid="class-option-3"
              value="Class 3"
              role="option"
            >
              Class 3
            </SelectItem>
            <SelectItem
              data-testid="class-option-4"
              value="Class 4"
              role="option"
            >
              Class 4
            </SelectItem>
            <SelectItem
              data-testid="class-option-5"
              value="Class 5"
              role="option"
            >
              Class 5
            </SelectItem>
            <SelectItem
              data-testid="class-option-6"
              value="Class 6"
              role="option"
            >
              Class 6
            </SelectItem>
            <SelectItem
              data-testid="class-option-7"
              value="Class 7"
              role="option"
            >
              Class 7
            </SelectItem>
            <SelectItem
              data-testid="class-option-8"
              value="Class 8"
              role="option"
            >
              Class 8
            </SelectItem>
            <SelectItem
              data-testid="class-option-9"
              value="Class 9"
              role="option"
            >
              Class 9
            </SelectItem>
            <SelectItem
              data-testid="class-option-10"
              value="Class 10"
              role="option"
            >
              Class 10
            </SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.section} onValueChange={handleSectionChange}>
          <SelectTrigger
            data-testid="section-select"
            className="w-[180px]"
            aria-label="Section"
            aria-labelledby="section-label"
          >
            <SelectValue placeholder="Select section" />
          </SelectTrigger>
          <SelectContent data-testid="section-content">
            <SelectItem data-testid="section-option-a" value="A" role="option">
              Section A
            </SelectItem>
            <SelectItem data-testid="section-option-b" value="B" role="option">
              Section B
            </SelectItem>
            <SelectItem data-testid="section-option-c" value="C" role="option">
              Section C
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Admission No.</TableHead>
            <TableHead>Name</TableHead>
            <TableHead id="class-label">Class</TableHead>
            <TableHead id="section-label">Section</TableHead>
            <TableHead>Roll No.</TableHead>
            <TableHead>Parent Name</TableHead>
            <TableHead>Contact</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students?.map((student: Student) => (
            <TableRow key={student.id}>
              <TableCell>{student.admission_number}</TableCell>
              <TableCell>{`${student.first_name} ${student.last_name}`}</TableCell>
              <TableCell>{student.class_name}</TableCell>
              <TableCell>{student.section}</TableCell>
              <TableCell>{student.roll_number}</TableCell>
              <TableCell>{student.parent_name}</TableCell>
              <TableCell>{student.parent_phone}</TableCell>
              <TableCell>
                <Button variant="ghost" size="sm">
                  View
                </Button>
                <Button variant="ghost" size="sm">
                  Edit
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
