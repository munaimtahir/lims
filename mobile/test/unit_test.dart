import 'package:flutter_test/flutter_test.dart';
import 'package:lims_mobile/utils/errors.dart';
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
}
