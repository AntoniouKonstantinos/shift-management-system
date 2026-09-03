import { Routes } from '@angular/router';
import { StaffComponent } from './features/staff/staff.component';
import { ScheduleComponent } from './features/schedule/schedule.component';

export const routes: Routes = [
  { path: '', component: ScheduleComponent },
  { path: 'staff', component: StaffComponent },
];
