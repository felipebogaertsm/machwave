import Head from 'next/head'
import Image from 'next/image'
import styles from '../styles/Home.module.css'

export default function Home() {
    return (
        <div class="col-sm-12 col-md-8 m-auto">

            <h1 class="py-4">Home page</h1>

            <h3>Welcome!</h3>

            <h5>Design a solid rocket motor right from your own web browser.</h5>

            <div class="container">
                <div class="row justify-content-center">
                    <a class="btn btn-primary col-4 p-4 fs-5">Start by creating an account</a>
                </div>
            </div>

        </div >
    )
}
