import { Routes } from '@angular/router';
import { StaffComponent } from './features/staff/staff.component';

export const routes: Routes = [
  { path: 'staff', component: StaffComponent },
  { path: '', redirectTo: 'staff', pathMatch: 'full' },
];
