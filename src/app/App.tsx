import { Outlet } from 'react-router-dom'
import { Suspense } from 'react'
import '../assets/styles/App.css'
import '../assets/styles/content.css'
import Footer from './components/footer'
import Header from './components/header'

function Loading() {
    return <h2>🌀 Loading...</h2>;
}

function App() {

    return (
        <>
            <Header />
            <Suspense fallback={<Loading />}>
                <div id="content">
                    <Outlet />
                </div>
            </Suspense>
            <Footer />
        </>
    )
}

export default App
