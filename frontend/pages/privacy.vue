<template>
    <div class="prose max-w-3xl mx-auto py-8 text-cs-whiteish">
        <h1 class="text-3xl font-bold mb-4">Privacy Policy</h1>

        <p class="mb-4 text-sm text-cs-whiteish/80">
            Last updated: {{ lastUpdated }}
        </p>

        <p class="mb-4">
            This page explains how <strong>Circuit Scope</strong> ("we") handles personal data when you use the
            Circuit Scope website and PCB review service (the "Service"). We keep this policy short and focused on
            what is strictly necessary to run the Service.
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-2">1. Who operates Circuit Scope</h2>
        <p class="mb-4">
            The Service is operated under the name <strong>Circuit Scope</strong>. If you have any questions about this
            policy or want to exercise your privacy rights, please
            <a class="underline" href="mailto:sara.elhark@gmail.com">email us</a>.
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-2">2. Data we process</h2>
        <p class="mb-2">
            We only collect data that is needed to provide the Service, keep it secure, and understand how it is used.
        </p>
        <ul class="list-disc list-inside space-y-2 mb-4">
            <li>
                <strong>Account data.</strong> When you sign in with Google or GitHub, we receive basic profile
                information from your provider (such as name, email address, avatar, and provider ID). This is used to
                create and maintain your account and to show your name/avatar next to the content you post.
            </li>
            <li>
                <strong>Project data.</strong> When you upload KiCad projects or screenshots/pictures, we process the
                files to generate preview
                assets (for example SVGs and 3D models) that are required for the review features. Original KiCad source
                files are only used for this processing step and are not stored long term. The generated preview assets
                may be stored as long as the related project is available on the Service.
            </li>
            <li>
                <strong>Public content.</strong> Projects you upload and comments you post are public by design and can
                be
                viewed by anyone, including users who are not logged in. Please do not post personal data in project
                titles, descriptions, or comments.
            </li>
            <li>
                <strong>Usage and log data.</strong> When you use the Service we may store limited technical logs such
                as
                IP address, browser information, and timestamps. This data is used for security, debugging, and abuse
                prevention and is typically kept for up to 30 days, unless we need it longer to investigate a specific
                issue.
            </li>
            <li>
                <strong>Product analytics.</strong> We use PostHog, a GDPR-compliant analytics tool, to understand how
                the
                Service is used and to improve it. We configure analytics to avoid tracking individual users more than
                necessary and do not use analytics data for advertising or selling profiles.
            </li>
        </ul>

        <h2 class="text-xl font-semibold mt-6 mb-2">3. Legal bases and purposes</h2>
        <p class="mb-4">
            We process personal data only for the following purposes:
        </p>
        <ul class="list-disc list-inside space-y-2 mb-4">
            <li>
                To provide, maintain, and improve the Service, including authentication, project uploads, rendering
                and display of PCB previews, and public comments.
            </li>
            <li>To secure the Service, prevent abuse, and debug technical issues.</li>
            <li>To understand overall usage of the Service via privacy-conscious analytics.</li>
        </ul>
        <p class="mb-4">
            Where applicable, these activities are based on the necessity to perform our agreement with you to
            provide the Service or on our legitimate interest in operating and improving a stable, secure platform.
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-2">4. Cookies and similar technologies</h2>
        <p class="mb-4">
            We use technical cookies or similar storage only where it is strictly necessary to provide core
            authentication and security features. We do not use cookies for advertising.
        </p>
        <p class="mb-4">
            PostHog analytics is configured to be privacy-friendly and not to track individuals more than required to
            understand general product usage.
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-2">5. Data sharing</h2>
        <p class="mb-4">
            We do not sell personal data.
        </p>
        <p class="mb-4">
            We may share limited data with service providers that help us operate the Service, for example:
        </p>
        <ul class="list-disc list-inside space-y-2 mb-4">
            <li>Hosting and storage providers that run our infrastructure.</li>
            <li>Authentication providers (Google and GitHub OAuth) when you choose to sign in with them.</li>
            <li>PostHog for product analytics.</li>
        </ul>
        <p class="mb-4">
            We may also disclose data if required by applicable law or to protect the rights, property, or safety of
            Circuit Scope, our users, or others.
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-2">6. Public projects and comments</h2>
        <p class="mb-4">
            The Service is a public community for sharing and reviewing PCB designs. Projects, preview assets, and
            comments are generally visible to everyone. Do not upload content that you are not allowed to share or that
            contains personal data about yourself or others.
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-2">7. Your rights</h2>
        <p class="mb-4">
            Depending on your location, you may have rights such as access, correction, deletion, and restriction of
            processing of your personal data. You can also object to certain processing activities where allowed by
            law.
        </p>
        <p class="mb-4">
            To exercise these rights, please
            <a class="underline" href="mailto:sara.elhark@gmail.com">email us</a>
            and we will handle your request as required by applicable law.
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-2">8. Children</h2>
        <p class="mb-4">
            The Service is not intended for children under 16 years of age. If you are under 16, you should not use
            the Service. If we learn that we have collected personal data from a child under 16, we will take reasonable
            steps to delete it.
        </p>

        <h2 class="text-xl font-semibold mt-6 mb-2">9. Changes to this policy</h2>
        <p class="mb-4">
            We may update this Privacy Policy from time to time to reflect changes to the Service or applicable law.
            When we make changes, we will update the "Last updated" date at the top of this page. If the changes are
            significant, we may also provide additional notice within the Service.
        </p>
    </div>
</template>

<script setup lang="ts">
const lastUpdated = 'December 2025'

defineOgImageComponent('OgTemplate', {
    heading: 'Privacy Policy',
    description: 'Learn how Circuit Scope handles your personal data and protects your privacy.',
})
</script>
