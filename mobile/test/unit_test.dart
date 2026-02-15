import 'package:flutter_test/flutter_test.dart';
import 'package:lims_mobile/utils/errors.dart';
import 'package:lims_mobile/domain/entities/user.dart';
import 'package:dio/dio.dart';

void main() {
  group('AppError Mapping Tests', () {
    test('Should map 401 to Session Expired', () {
      final dioError = DioException(
        requestOptions: RequestOptions(path: ''),
        response: Response(
          requestOptions: RequestOptions(path: ''),
          statusCode: 401,
        ),
        type: DioExceptionType.badResponse,
      );

      final appError = AppError.fromDio(dioError);
      expect(appError.message, contains('Session expired'));
    });

    test('Should map connection timeout', () {
      final dioError = DioException(
        requestOptions: RequestOptions(path: ''),
        type: DioExceptionType.connectionTimeout,
      );

      final appError = AppError.fromDio(dioError);
      expect(appError.message, contains('timed out'));
    });
    
    test('Should use custom message from backend if available', () {
      final dioError = DioException(
        requestOptions: RequestOptions(path: ''),
        response: Response(
          requestOptions: RequestOptions(path: ''),
          statusCode: 400,
          data: {'message': 'Invalid patient data'},
        ),
        type: DioExceptionType.badResponse,
      );

      final appError = AppError.fromDio(dioError);
      expect(appError.message, 'Invalid patient data');
    });
  });

  group('Model Parsing Tests', () {
    test('UserMe fromJson should work', () {
      final json = {
        'id': '123',
        'name': 'Test User',
        'roles': ['admin', 'lab_manager'],
        'tenantId': 'T1',
      };
      
      final user = UserMe.fromJson(json);
      expect(user.id, '123');
      expect(user.roles, contains('admin'));
    });

    test('TenantSettings default values', () {
      final settings = TenantSettings.fromJson({});
      expect(settings.sampleWorkflowEnabled, isTrue);
      expect(settings.billingEnabled, isTrue);
    });
  });
}
