import { Injectable, signal } from '@angular/core';
import { Observable, Subject } from 'rxjs';

/**
 * WebSocket connection state
 */
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * Base WebSocket service providing generic WebSocket infrastructure
 * Can be extended by feature-specific WebSocket services
 * 
 * Modern Angular 20 with signals for reactive state
 */
@Injectable({
  providedIn: 'root'
})
export class WebSocketBaseService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelay = 3000; // ms
  private reconnectTimeout: any;

  // Reactive state using signals
  readonly connectionState = signal<WebSocketState>('disconnected');
  readonly isConnected = signal<boolean>(false);

  // Message streams
  private messageSubject = new Subject<any>();
  readonly messages$ = this.messageSubject.asObservable();

  /**
   * Connect to WebSocket server
   */
  connect(url: string): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.connectionState.set('connecting');
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.connectionState.set('connected');
      this.isConnected.set(true);
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event: MessageEvent) => {
      this.onMessage(event);
    };

    this.socket.onclose = (event: CloseEvent) => {
      this.onClose(event);
    };

    this.socket.onerror = (error: Event) => {
      this.onError(error);
    };
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.connectionState.set('disconnected');
    this.isConnected.set(false);
    this.reconnectAttempts = 0;
  }

  /**
   * Send message through WebSocket
   */
  send(message: any): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return;
    }

    try {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      this.socket.send(data);
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(url: string): void {
    this.reconnectAttempts++;
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
    
    this.reconnectTimeout = setTimeout(() => {
      console.log('Attempting to reconnect...');
      this.connect(url);
    }, this.reconnectDelay);
  }

  /**
   * Get current connection state
   */
  getConnectionState(): WebSocketState {
    return this.connectionState();
  }

  /**
   * Check if connected
   */
  isSocketConnected(): boolean {
    return this.isConnected();
  }

  /**
   * Handle incoming message (can be overridden)
   */
  protected onMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      this.messageSubject.next(data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket close (can be overridden)
   */
  protected onClose(event: CloseEvent): void {
    console.log('WebSocket disconnected', event);
    this.connectionState.set('disconnected');
    this.isConnected.set(false);
    
    // Attempt reconnection if not a normal closure
    if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect(event.target ? (event.target as any).url : '');
    }
  }

  /**
   * Handle WebSocket error (can be overridden)
   */
  protected onError(error: Event): void {
    console.error('WebSocket error:', error);
    this.connectionState.set('error');
    this.isConnected.set(false);
  }

  /**
   * Store last URL for reconnection
   */
  private lastUrl?: string;

  /**
   * Updated connect to store URL
   */
  private scheduleReconnectWithUrl(url: string): void {
    this.lastUrl = url;
    this.scheduleReconnect(url);
  }
}

