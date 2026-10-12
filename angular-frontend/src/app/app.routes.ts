import { Routes } from '@angular/router';
import { ScheduleComponent } from './features/schedule/schedule.component';
import { StaffComponent } from './features/staff/staff.component';
import { TimeOffComponent } from './features/time-off/time-off.component';

export const routes: Routes = [
  { path: '', component: ScheduleComponent },
  { path: 'staff', component: StaffComponent },
  { path: 'time-off', component: TimeOffComponent },
  { path: '**', redirectTo: '' },
];
