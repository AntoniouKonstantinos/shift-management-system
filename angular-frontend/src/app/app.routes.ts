import { Routes } from '@angular/router';
import { ScheduleComponent } from './features/schedule/schedule.component';
import { StaffComponent } from './features/staff/staff.component';
import { TimeOffComponent } from './features/time-off/time-off.component';
import { LoginComponent } from './features/login/login.component';
import { authGuard, managerGuard, guestGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent, canActivate: [guestGuard] },
  { path: '', component: ScheduleComponent, canActivate: [authGuard] },
  { path: 'staff', component: StaffComponent, canActivate: [managerGuard] },
  { path: 'time-off', component: TimeOffComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: '' },
];
