export interface Availability {
  id: number;
  employee_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  ends_next_day: boolean;
}

export interface AvailabilityCreate {
  day_of_week: number;
  start_time: string;
  end_time: string;
}

export interface AvailabilityUpdate {
  day_of_week?: number;
  start_time?: string;
  end_time?: string;
}

export const DAY_NAMES = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
];
