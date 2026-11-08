import { HttpClient } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { AuthService } from '../../core/auth.service';
import { Health } from '../../core/models';

@Component({
  selector: 'app-home',
  templateUrl: './home.html',
})
export class Home {
  protected readonly auth = inject(AuthService);
  protected readonly health = toSignal(inject(HttpClient).get<Health>('/api/health'));
}
