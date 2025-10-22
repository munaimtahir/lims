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
        <p>
          This is the starter dashboard for the Laboratory Information Management System.
        </p>
        <p>
          <Link href={`${process.env.NEXT_PUBLIC_API_URL}/health`}>Check API Health</Link>
        </p>
      </main>
    </div>
  );
};

export default HomePage;
