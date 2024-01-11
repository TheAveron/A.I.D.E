import { Outlet } from 'react-router-dom'
import '../assets/styles/App.css'
import Footer from './components/footer'
import Header from './components/header'


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
