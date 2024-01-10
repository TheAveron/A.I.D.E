import { Outlet } from 'react-router-dom'
import '../assets/styles/App.css'
import Header from './components/header'
import Footer from './components/footer'

function App() {

    return (
        <>
            <Header />
            <div id="content">
                <Outlet />
            </div>
            <Footer />
        </>
    )
}

export default App
