import { NuxtAuthHandler } from "#auth";
import Credentials from "next-auth/providers/credentials";

const runtimeConfig = useRuntimeConfig();

export default NuxtAuthHandler({
    secret: runtimeConfig.auth.secret,
    providers: [
        // @ts-expect-error https://auth.sidebase.io/guide/authjs/quick-start#configuration
        Credentials.default({
            id: "credentials",
            credentials: {},
            authorize() {
                return {
                    id: "1",
                    name: "John Doe",
                    email: "johndoe@example.com",
                };
            },
        }),
    ],
    jwt: {
        async encode({ secret, token, maxAge }) {
            return JWTUtils.encode(
                token,
                secret,
                runtimeConfig.auth.sign,
                maxAge || runtimeConfig.auth.maxAge,
            );
        },

        async decode({ secret, token }) {
            return JWTUtils.decode(secret, token, runtimeConfig.auth.sign);
        },
    },
    callbacks: {
        jwt({ token, user }) {
            if (user) {
                token.id = user.id;
                token.email = user.email;
                token.name = user.name;
            }

            return token;
        },

        async session({ session, token }) {
            if (session.user) {
                if (token.id) {
                    session.user.id = token.id;
                }

                if (token.email) {
                    session.user.email = token.email;
                }

                if (token.name) {
                    session.user.name = token.name;
                }
            }

            session.accessToken = await JWTUtils.encode(
                token,
                runtimeConfig.auth.secret,
                runtimeConfig.auth.sign,
                runtimeConfig.auth.maxAge,
            );

            return session;
        },
    },
});
