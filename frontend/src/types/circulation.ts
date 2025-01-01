export interface BookCirculation {
  id: number;
  book: {
    id: number;
    title: string;
    author: string;
    isbn: string;
  };
  member: {
    id: number;
    user: {
      id: number;
      first_name: string;
      last_name: string;
      email: string;
    };
    admission_number: string;
  };
  issue_date: string;
  due_date: string;
  return_date: string | null;
  status: 'issued' | 'returned' | 'overdue';
  fine_amount: number;
}
