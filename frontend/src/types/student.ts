export interface Student {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  registration_number: string;
  class_section?: string;
  admission_date: string;
  status: 'active' | 'inactive' | 'graduated';
}
