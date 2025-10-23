import Head from 'next/head';
import Link from 'next/link';

const HomePage = () => {
  return (
    <div style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
      <Head>
        <title>LIMS — Demo Dashboard</title>
      </Head>
      <main>
        <h1>LIMS — Demo Dashboard</h1>
        <p>This is the starter dashboard for the Laboratory Information Management System.</p>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          <li style={{ marginBottom: '0.5rem' }}>
            <Link href="/patients">
              <a style={{ color: '#007bff', textDecoration: 'none', fontSize: '1.1rem' }}>
                → Patient Management
              </a>
            </Link>
          </li>
          <li>
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL}/health`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#007bff', textDecoration: 'none', fontSize: '1.1rem' }}
            >
              → Check API Health
            </a>
          </li>
        </ul>
      </main>
    </div>
  );
};

export default HomePage;
