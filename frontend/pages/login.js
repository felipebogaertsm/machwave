// -* - coding: utf - 8 -* -
// Author: Felipe Bogaerts de Mattos
// Contact me at felipe.bogaerts@engenharia.ufjf.br.
// This program is free software: you can redistribute it and / or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.

// Components:
import Card from '../components/Card'
import FormControl from '../components/FormControl'
import Button from '../components/Button'
import Subheading from '../components/Subheading'
import NavbarPage from '../components/NavbarPage'

export default function Login() {
    return (
        <NavbarPage>
            <div className='mt-10'>
                <div className='w-[90%] h-full mx-auto lg:w-[60%] xl:w-[60%] grid place-content-center'>
                    <Card className='min-w-[40vw]'>
                        <Subheading className='my-2'>Login</Subheading>

                        <div className='mb-2'>
                            <FormControl title='Email' />
                        </div>
                        <div>
                            <FormControl title='Password' type='password' />
                        </div>

                        <div className='flex justify-center mt-4'>
                            <Button type='submit'>Submit</Button>
                        </div>
                    </Card>
                </div>
            </div >
        </NavbarPage>
    )
}
