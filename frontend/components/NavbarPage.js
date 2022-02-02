// Components:
import Navbar from '../components/Navbar'

function NavbarPage({ children }) {
    return (
        <div>
            <Navbar />

            <div>
                {children}
            </div>
        </div>
    )
}

export default NavbarPage
