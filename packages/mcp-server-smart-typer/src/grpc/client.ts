import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { 
  GrpcConnectionError, 
  UIAutomationError,
  TypeTextRequest,
  TypeTextResponse,
  SendKeysRequest,
  SendKeysResponse,
  GetActiveWindowRequest,
  GetActiveWindowResponse,
  FindElementRequest,
  FindElementResponse,
  ClickElementRequest,
  ClickElementResponse,
  ServerConfig
} from '../types/index.js';
import { logger } from '../utils/logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Default configuration
const DEFAULT_CONFIG: ServerConfig = {
  grpcHost: 'localhost',
  grpcPort: 50051,
  timeout: 30000, // 30 seconds
};

export class GrpcClient {
  private client: any;
  private config: ServerConfig;
  private isConnected: boolean = false;

  constructor(config?: Partial<ServerConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  async connect(): Promise<void> {
    try {
      logger.info('Connecting to native helper gRPC service...');
      
      // Load the protobuf definition
      const protoPath = join(__dirname, '../../proto/ui_automation.proto');
      logger.debug('Loading proto file from:', protoPath);
      
      const packageDefinition = protoLoader.loadSync(protoPath, {
        keepCase: true,
        longs: String,
        enums: String,
        defaults: true,
        oneofs: true,
      });

      const proto = grpc.loadPackageDefinition(packageDefinition) as any;
      
      // Create the gRPC client
      this.client = new proto.ui_automation.UIAutomationService(
        `${this.config.grpcHost}:${this.config.grpcPort}`,
        grpc.credentials.createInsecure()
      );

      // Test the connection
      await this.waitForConnection();
      this.isConnected = true;
      
      logger.info(`Connected to gRPC service at ${this.config.grpcHost}:${this.config.grpcPort}`);
    } catch (error) {
      logger.error('Failed to connect to gRPC service:', error);
      throw new GrpcConnectionError(
        `Failed to connect to native helper service: ${error instanceof Error ? error.message : String(error)}`,
        error instanceof Error ? error : undefined
      );
    }
  }

  async disconnect(): Promise<void> {
    if (this.client && this.isConnected) {
      try {
        this.client.close();
        this.isConnected = false;
        logger.info('Disconnected from gRPC service');
      } catch (error) {
        logger.warn('Error during gRPC disconnect:', error);
      }
    }
  }

  private async waitForConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      const deadline = Date.now() + this.config.timeout;
      
      this.client.waitForReady(deadline, (error: Error | null) => {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  private async callRpc<TRequest, TResponse>(
    methodName: string,
    request: TRequest
  ): Promise<TResponse> {
    if (!this.isConnected) {
      throw new GrpcConnectionError('gRPC client is not connected');
    }

    return new Promise((resolve, reject) => {
      const deadline = Date.now() + this.config.timeout;
      
      this.client[methodName](request, { deadline }, (error: Error | null, response: TResponse) => {
        if (error) {
          logger.error(`gRPC call ${methodName} failed:`, error);
          reject(new UIAutomationError(
            `UI automation call ${methodName} failed: ${error.message}`,
            error
          ));
        } else {
          logger.debug(`gRPC call ${methodName} succeeded:`, response);
          resolve(response);
        }
      });
    });
  }

  async typeText(request: TypeTextRequest): Promise<TypeTextResponse> {
    logger.debug('Calling typeText:', request);
    return this.callRpc<TypeTextRequest, TypeTextResponse>('typeText', request);
  }

  async sendKeys(request: SendKeysRequest): Promise<SendKeysResponse> {
    logger.debug('Calling sendKeys:', request);
    return this.callRpc<SendKeysRequest, SendKeysResponse>('sendKeys', request);
  }

  async getActiveWindow(request: GetActiveWindowRequest): Promise<GetActiveWindowResponse> {
    logger.debug('Calling getActiveWindow:', request);
    return this.callRpc<GetActiveWindowRequest, GetActiveWindowResponse>('getActiveWindow', request);
  }

  async findElement(request: FindElementRequest): Promise<FindElementResponse> {
    logger.debug('Calling findElement:', request);
    return this.callRpc<FindElementRequest, FindElementResponse>('findElement', request);
  }

  async clickElement(request: ClickElementRequest): Promise<ClickElementResponse> {
    logger.debug('Calling clickElement:', request);
    return this.callRpc<ClickElementRequest, ClickElementResponse>('clickElement', request);
  }

  isReady(): boolean {
    return this.isConnected;
  }
}
