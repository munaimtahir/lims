import { expect, test } from '@playwright/test';

// This test requires backend and frontend to be running
// Backend: python manage.py runserver (on localhost:8000)
// Frontend: pnpm dev (on localhost:5173)

// E2E tests always use the full backend URL for API requests
// Environment variable can override the default localhost:8000
const API_BASE_URL = process.env.E2E_API_BASE_URL || 'http://localhost:8000';
const API_URL = `${API_BASE_URL}/api`;

test.describe('LIMS Complete Workflow', () => {
  test('full workflow: register patient → order → sample → result → report', async ({ request }) => {
    // 1. Login as admin
    const loginResponse = await request.post(`${API_URL}/auth/login/`, {
      data: {
        username: 'admin',
        password: 'admin123',
      },
    });
    expect(loginResponse.ok()).toBeTruthy();
    const { access } = await loginResponse.json();
    expect(access).toBeTruthy();

    // Set authorization header for subsequent requests
    const headers = { Authorization: `Bearer ${access}` };

    // 2. Create a patient
    const patientResponse = await request.post(`${API_URL}/patients/`, {
      headers,
      data: {
        full_name: 'Test Patient E2E',
        father_name: 'Test Father',
        dob: '1990-01-01',
        sex: 'M',
        phone: '03001234599',
        cnic: '12345-1234599-1',
        address: '123 Test Street',
      },
    });
    expect(patientResponse.ok()).toBeTruthy();
    const patient = await patientResponse.json();
    expect(patient.mrn).toBeTruthy();
    console.log('Created patient:', patient.mrn);

    // 3. Get test catalog
    const catalogResponse = await request.get(`${API_URL}/catalog/`, { headers });
    expect(catalogResponse.ok()).toBeTruthy();
    const catalogData = await catalogResponse.json();
    expect(catalogData.results.length).toBeGreaterThan(0);
    const testId = catalogData.results[0].id;
    console.log('Using test:', catalogData.results[0].name);

    // 4. Create an order
    const orderResponse = await request.post(`${API_URL}/orders/`, {
      headers,
      data: {
        patient: patient.id,
        priority: 'ROUTINE',
        test_ids: [testId],
      },
    });
    expect(orderResponse.ok()).toBeTruthy();
    const order = await orderResponse.json();
    expect(order.order_no).toBeTruthy();
    expect(order.items.length).toBe(1);
    console.log('Created order:', order.order_no);

    // 5. Create a sample
    const orderItemId = order.items[0].id;
    const sampleResponse = await request.post(`${API_URL}/samples/`, {
      headers,
      data: {
        order_item: orderItemId,
        sample_type: 'Blood',
      },
    });
    expect(sampleResponse.ok()).toBeTruthy();
    const sample = await sampleResponse.json();
    expect(sample.barcode).toBeTruthy();
    console.log('Created sample:', sample.barcode);

    // 6. Collect the sample
    const collectResponse = await request.post(`${API_URL}/samples/${sample.id}/collect/`, { headers });
    expect(collectResponse.ok()).toBeTruthy();
    const collectedSample = await collectResponse.json();
    expect(collectedSample.status).toBe('COLLECTED');
    console.log('Sample collected');

    // 7. Receive the sample
    const receiveResponse = await request.post(`${API_URL}/samples/${sample.id}/receive/`, { headers });
    expect(receiveResponse.ok()).toBeTruthy();
    const receivedSample = await receiveResponse.json();
    expect(receivedSample.status).toBe('RECEIVED');
    console.log('Sample received');

    // 8. Create a result
    const resultResponse = await request.post(`${API_URL}/results/`, {
      headers,
      data: {
        order_item: orderItemId,
        value: '12.5',
        unit: 'g/dL',
        reference_range: '12-16',
        flags: 'N',
      },
    });
    expect(resultResponse.ok()).toBeTruthy();
    const result = await resultResponse.json();
    expect(result.value).toBe('12.5');
    console.log('Created result');

    // 9. Enter the result
    const enterResponse = await request.post(`${API_URL}/results/${result.id}/enter/`, { headers });
    expect(enterResponse.ok()).toBeTruthy();
    const enteredResult = await enterResponse.json();
    expect(enteredResult.status).toBe('ENTERED');
    console.log('Result entered');

    // 10. Verify the result
    const verifyResponse = await request.post(`${API_URL}/results/${result.id}/verify/`, { headers });
    expect(verifyResponse.ok()).toBeTruthy();
    const verifiedResult = await verifyResponse.json();
    expect(verifiedResult.status).toBe('VERIFIED');
    console.log('Result verified');

    // 11. Publish the result
    const publishResponse = await request.post(`${API_URL}/results/${result.id}/publish/`, { headers });
    expect(publishResponse.ok()).toBeTruthy();
    const publishedResult = await publishResponse.json();
    expect(publishedResult.status).toBe('PUBLISHED');
    console.log('Result published');

    // 12. Generate report
    const reportResponse = await request.post(`${API_URL}/reports/generate/${order.id}/`, { headers });
    expect(reportResponse.ok()).toBeTruthy();
    const report = await reportResponse.json();
    expect(report.pdf_file).toBeTruthy();
    console.log('Report generated:', report.pdf_file);

    // 13. Download report
    const downloadResponse = await request.get(`${API_URL}/reports/${report.id}/download/`, { headers });
    expect(downloadResponse.ok()).toBeTruthy();
    const pdfBuffer = await downloadResponse.body();
    expect(pdfBuffer).toBeTruthy();
    expect(pdfBuffer.length).toBeGreaterThan(0);
    console.log('Report downloaded, size:', pdfBuffer.length, 'bytes');

    console.log('\n✅ Complete workflow test passed!');
  });

  test('authentication flow', async ({ request }) => {
    // Test login
    const loginResponse = await request.post(`${API_URL}/auth/login/`, {
      data: {
        username: 'admin',
        password: 'admin123',
      },
    });
    expect(loginResponse.ok()).toBeTruthy();
    const { access, refresh, role, username } = await loginResponse.json();
    expect(access).toBeTruthy();
    expect(refresh).toBeTruthy();
    expect(role).toBe('ADMIN');
    expect(username).toBe('admin');

    // Test token refresh
    const refreshResponse = await request.post(`${API_URL}/auth/refresh/`, {
      data: { refresh },
    });
    expect(refreshResponse.ok()).toBeTruthy();
    const { access: newAccess } = await refreshResponse.json();
    expect(newAccess).toBeTruthy();
    expect(newAccess).not.toBe(access); // New token should be different

    // Test logout
    const logoutResponse = await request.post(`${API_URL}/auth/logout/`, {
      headers: { Authorization: `Bearer ${access}` },
      data: { refresh },
    });
    expect(logoutResponse.ok()).toBeTruthy();
  });

  test('RBAC enforcement', async ({ request }) => {
    // Login as reception
    const loginResponse = await request.post(`${API_URL}/auth/login/`, {
      data: {
        username: 'reception',
        password: 'reception123',
      },
    });
    expect(loginResponse.ok()).toBeTruthy();
    const { access } = await loginResponse.json();

    // Reception can create patients
    const patientResponse = await request.post(`${API_URL}/patients/`, {
      headers: { Authorization: `Bearer ${access}` },
      data: {
        full_name: 'RBAC Test Patient',
        father_name: 'Test Father',
        dob: '1995-01-01',
        sex: 'F',
        phone: '03001234598',
        cnic: '12345-1234598-1',
        address: '456 Test Street',
      },
    });
    expect(patientResponse.ok()).toBeTruthy();

    // But reception cannot verify results (requires pathologist)
    const verifyResponse = await request.post(`${API_URL}/results/1/verify/`, {
      headers: { Authorization: `Bearer ${access}` },
    });
    expect(verifyResponse.status()).toBe(403); // Forbidden
  });
});

test.describe('Accessibility', () => {
  test('health endpoint is accessible', async ({ request }) => {
    const response = await request.get(`${API_URL}/health/`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });
});
