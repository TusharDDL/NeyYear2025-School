'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import { BookCirculation as IBookCirculation } from '@/types/circulation';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function BookCirculation() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState('all'); // all, overdue, returned

  const { data: circulations = [], isLoading } = useQuery({
    queryKey: ['circulations', filter],
    queryFn: async () => {
      if (filter === 'overdue') {
        const response = await apiClient.getOverdueBooks();
        return response.data;
      }
      // For testing purposes, fetch all records
      const response = await fetch('/api/books/circulation');
      const data = await response.json();
      return data.data;
    },
  });

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Select value={filter} onValueChange={setFilter} aria-label="Filter circulation records">
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter records" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Records</SelectItem>
            <SelectItem value="overdue">Overdue Books</SelectItem>
            <SelectItem value="returned">Returned Books</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Table role="table" aria-label="Book circulation records">
        <TableHeader>
          <TableRow>
            <TableHead>Book Title</TableHead>
            <TableHead>Member</TableHead>
            <TableHead>Issue Date</TableHead>
            <TableHead>Due Date</TableHead>
            <TableHead>Return Date</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Fine</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {circulations?.map((circulation: IBookCirculation) => (
            <TableRow key={circulation.id}>
              <TableCell>{circulation.book.title}</TableCell>
              <TableCell>
                {`${circulation.member.user.first_name} ${circulation.member.user.last_name}`}
              </TableCell>
              <TableCell>{circulation.issue_date}</TableCell>
              <TableCell>{circulation.due_date}</TableCell>
              <TableCell>{circulation.return_date || '-'}</TableCell>
              <TableCell>{circulation.status}</TableCell>
              <TableCell>${circulation.fine_amount}</TableCell>
              <TableCell>
                {circulation.status === 'issued' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={async () => {
                      try {
                        await fetch(`/api/books/circulation/${circulation.id}/return`, {
                          method: 'POST',
                          headers: {
                            'Content-Type': 'application/json'
                          }
                        });
                        // Refetch the data using React Query instead of page reload
                        await queryClient.invalidateQueries({ queryKey: ['circulations'] });
                      } catch (error) {
                        console.error('Error returning book:', error);
                      }
                    }}
                  >
                    Return Book
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
