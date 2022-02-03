// -* - coding: utf - 8 -* -
// Author: Felipe Bogaerts de Mattos
// Contact me at felipe.bogaerts@engenharia.ufjf.br.
// This program is free software: you can redistribute it and / or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.

import { useRouter } from 'next/router'

// Components:
import Card from '../components/Card'
import Button from '../components/Button'
import Subheading from '../components/Subheading'
import NavbarPage from '../components/NavbarPage'

export default function Home() {
    const router = useRouter()

    return (
        <NavbarPage>
            <div className='mt-10'>
                <div className='w-[90%] h-full mx-auto lg:w-[60%] xl:w-[60%] grid place-content-center'>
                    <Card>
                        <Subheading className='my-2'>Welcome</Subheading>

                        <h5>Design a solid rocket motor right from your own web browser.</h5>

                        <div className='flex justify-center mt-4'>
                            <Button onClick={(e) => router.push('/login')}>Log in</Button>
                        </div>
                    </Card>
                </div>
            </div >
        </NavbarPage>
    )
}
