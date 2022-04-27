// Components:
import { AppBar, Container, Toolbar, Typography } from "@mui/material"

export default function Home() {
    return (
        <div>
            <div>
                <AppBar position="static">
                    <Container>
                        <Toolbar>
                            <Typography variant="h6">SRM SOLVER</Typography>
                        </Toolbar>
                    </Container>
                </AppBar>
            </div>
        </div>
    )
}
