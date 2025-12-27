export function CSVImportPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        Data Import Management
      </h1>

      <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg mb-6">
        <p className="font-medium">ℹ️ Information</p>
        <p className="mt-1 text-sm">
          Data import is currently handled via Django management commands. This
          provides better control and validation for large data imports.
        </p>
      </div>

      <div className="space-y-6">
        {/* LIMS Master Data Import */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            LIMS Master Data Import
          </h2>
          <p className="text-gray-600 mb-4">
            Import tests, parameters, test-parameter mappings, and reference
            ranges from the LIMS Master Excel file.
          </p>

          <div className="bg-gray-50 border border-gray-200 rounded p-4 mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              Source File
            </h3>
            <p className="text-sm text-gray-600 font-mono">
              backend/seed_data/AlShifa_LIMS_Master.xlsx
            </p>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded p-4 mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              Import Commands
            </h3>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-gray-600 mb-1">Test import first (dry-run):</p>
                <code className="block bg-gray-900 text-green-400 px-3 py-2 rounded text-xs overflow-x-auto">
                  docker compose exec backend python manage.py import_lims_master --dry-run
                </code>
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">Perform actual import:</p>
                <code className="block bg-gray-900 text-green-400 px-3 py-2 rounded text-xs overflow-x-auto">
                  docker compose exec backend python manage.py import_lims_master
                </code>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
            <h3 className="text-sm font-semibold text-yellow-800 mb-2">
              ⚠️ Important Notes
            </h3>
            <ul className="text-sm text-yellow-700 space-y-1 list-disc list-inside">
              <li>Always run with --dry-run first to validate data</li>
              <li>The command imports: Tests, Parameters, TestParameters, and ReferenceRanges</li>
              <li>Existing records with the same code will be updated</li>
              <li>Backup your database before importing</li>
            </ul>
          </div>
        </div>

        {/* Test Catalog Import */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Test Catalog Quick Import
          </h2>
          <p className="text-gray-600 mb-4">
            Import or update test catalog entries using CSV format.
          </p>

          <div className="bg-gray-50 border border-gray-200 rounded p-4 mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              CSV Format (Required Columns)
            </h3>
            <code className="block bg-gray-900 text-green-400 px-3 py-2 rounded text-xs overflow-x-auto">
              code,name,category,sample_type,price,turnaround_time_hours,is_active
            </code>
            <p className="text-xs text-gray-600 mt-2">
              Example: CBC,Complete Blood Count,Hematology,Blood,1500,24,True
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded p-4">
            <p className="text-sm text-blue-700">
              💡 Tip: Use the admin interface to manually add or update test
              catalog entries, or prepare a CSV file according to the format
              above for bulk import.
            </p>
          </div>
        </div>

        {/* Parameters Import */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Parameters Import
          </h2>
          <p className="text-gray-600 mb-4">
            Import parameter definitions for test results.
          </p>

          <div className="bg-gray-50 border border-gray-200 rounded p-4 mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              CSV Format (Required Columns)
            </h3>
            <code className="block bg-gray-900 text-green-400 px-3 py-2 rounded text-xs overflow-x-auto">
              code,name,unit,data_type,decimal_places,active
            </code>
            <p className="text-xs text-gray-600 mt-2">
              Example: HGB,Hemoglobin,g/dL,Numeric,1,True
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded p-4">
            <p className="text-sm text-blue-700">
              💡 Note: Parameters are best imported via the LIMS Master import
              which includes reference ranges and test-parameter mappings.
            </p>
          </div>
        </div>

        {/* Reference Ranges Import */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Reference Ranges Import
          </h2>
          <p className="text-gray-600 mb-4">
            Import reference ranges for different parameters based on age, sex,
            and population groups.
          </p>

          <div className="bg-gray-50 border border-gray-200 rounded p-4 mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              CSV Format (Required Columns)
            </h3>
            <code className="block bg-gray-900 text-green-400 px-3 py-2 rounded text-xs overflow-x-auto">
              parameter_code,sex,age_min,age_max,age_unit,normal_low,normal_high,unit
            </code>
            <p className="text-xs text-gray-600 mt-2">
              Example: HGB,M,18,999,Years,13.5,17.5,g/dL
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded p-4">
            <p className="text-sm text-blue-700">
              💡 Note: Reference ranges are automatically imported with the LIMS
              Master data import command.
            </p>
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Alternative: Manual Management
          </h2>
          <p className="text-gray-600 mb-4">
            For individual records or small updates, use the admin pages:
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href="/admin/tests"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              Manage Tests
            </a>
            <a
              href="/admin/parameters"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              Manage Parameters
            </a>
            <a
              href="/admin/test-parameters"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
            >
              Manage Test-Parameters
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
