// -* - coding: utf - 8 -* -
// Author: Felipe Bogaerts de Mattos
// Contact me at felipe.bogaerts@engenharia.ufjf.br.
// This program is free software: you can redistribute it and / or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.

// Components:
import NavbarItem from "./navbarItem"
import NavbarLogo from "./navbarLogo"

export default function Navbar() {
    return (
        <div className='
                top-0 h-16 bg-slate-900 text-white w-full px-10 py-3
            '
        >
            <div className='
                    flex flex-row space-x-4 h-full w-full
                '
            >
                <NavbarLogo>SRM Solver</NavbarLogo>
                <div className='grow'></div>
                <NavbarItem>Modeler</NavbarItem>
                <NavbarItem>Simulations</NavbarItem>
                <NavbarItem>Code</NavbarItem>
            </div>
        </div>
    )
}