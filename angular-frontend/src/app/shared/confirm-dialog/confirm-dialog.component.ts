import { Component, ElementRef, HostListener, effect, viewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ConfirmService } from '../../core/services/confirm.service';

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './confirm-dialog.component.html',
  styleUrl: './confirm-dialog.component.css',
})
export class ConfirmDialogComponent {
  private cancelButton = viewChild<ElementRef<HTMLButtonElement>>('cancelButton');

  constructor(public confirmService: ConfirmService) {
    effect(() => {
      this.cancelButton()?.nativeElement.focus();
    });
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.confirmService.answer(false);
  }

  onBackdropClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) {
      this.confirmService.answer(false);
    }
  }
}
