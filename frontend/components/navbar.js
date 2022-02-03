// -* - coding: utf - 8 -* -
// Author: Felipe Bogaerts de Mattos
// Contact me at felipe.bogaerts@engenharia.ufjf.br.
// This program is free software: you can redistribute it and / or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.

import { useRouter } from "next/router"

// Components:
import NavbarItem from "./NavbarItem"
import NavbarLogo from "./NavbarLogo"

export default function Navbar() {
    const router = useRouter()

    return (
        <div className='
                top-0 h-16 bg-slate-900 text-white w-full px-10 py-3
                select-none border-b-2 border-white shadow-lg
            '
        >
            <div className='
                    flex flex-row space-x-4 h-full w-full
                '
            >
                <NavbarLogo onClick={(e) => router.push('/')}>SRM Solver</NavbarLogo >
                <div className='grow'></div>
                <NavbarItem>Builder</NavbarItem>
                <NavbarItem>Simulations</NavbarItem>
                <NavbarItem>Code</NavbarItem>
            </div>
        </div>
    )
}