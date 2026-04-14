import type { User } from "next-auth";
import { NuxtAuthHandler } from "#auth";
import { ResponseCodesRecord } from "#shared/utils/response-codes";
import { ApiErrorSchema } from "#shared/utils/schemas/api";
import { UserResponse } from "#shared/utils/schemas/auth";
import Credentials from "next-auth/providers/credentials";
import { FetchError } from "ofetch";

const runtimeConfig = useRuntimeConfig();

export default NuxtAuthHandler({
    secret: runtimeConfig.auth.SECRET,
    pages: {
        newUser: "/auth/sign-up",
        signIn: "/auth/sign-in",
    },
    providers: [
        // @ts-expect-error https://auth.sidebase.io/guide/authjs/quick-start#configuration
        Credentials.default({
            id: "credentials",
            credentials: {},
            async authorize(credentials: Record<"email" | "password", string>) {
                /**
                 * Any errors that may occur inside here should be thrown
                 * using simple
                 * ```typescript
                 * throw new Error('error:code')
                 * ```
                 *
                 * and will be parsed as followed
                 * ```typescript
                 * const response = await auth.signIn('credentials')
                 * if (response.error) // do something...
                 */

                const formData = new FormBuilder()
                    .append("email", credentials.email)
                    .append("password", credentials.password)
                    .build();

                try {
                    const response = await $fetch("/auth/sign-in", {
                        baseURL: runtimeConfig.public.API_BASE,
                        method: "POST",
                        body: formData,
                    });

                    const parsedResponse = UserResponse.safeParse(response);

                    if (!parsedResponse.success) {
                        throw new Error(ResponseCodesRecord.Server.Auth.SignIn.BadPayload);
                    }

                    return {
                        id: parsedResponse.data.id,
                        name: parsedResponse.data.name,
                        email: parsedResponse.data.email,
                        role: parsedResponse.data.role,
                    } satisfies User;
                } catch (error) {
                    if (error instanceof FetchError) {
                        const parsedError = ApiErrorSchema.safeParse(error.data);
                        if (!parsedError.success) {
                            return null;
                        }

                        throw new Error(parsedError.data.error);
                    }

                    return null;
                }
            },
        }),
    ],
    jwt: {
        async encode({ secret, token, maxAge }) {
            return JWTUtils.encode(
                token,
                secret,
                runtimeConfig.auth.SIGN,
                maxAge || runtimeConfig.auth.MAX_AGE,
            );
        },

        async decode({ secret, token }) {
            return JWTUtils.decode(secret, token, runtimeConfig.auth.SIGN);
        },
    },
    callbacks: {
        jwt({ token, user }) {
            if (user) {
                token.id = user.id;
                token.email = user.email;
                token.name = user.name;
                token.role = user.role;
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

                if (token.role) {
                    session.user.role = token.role;
                }
            }

            session.accessToken = await JWTUtils.encode(
                token,
                runtimeConfig.auth.SECRET,
                runtimeConfig.auth.SIGN,
                runtimeConfig.auth.MAX_AGE,
            );

            return session;
        },
    },
});
