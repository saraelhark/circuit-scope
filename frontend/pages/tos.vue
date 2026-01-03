<template>
  <div class="prose max-w-3xl mx-auto py-8 text-cs-whiteish">
    <h1 class="text-3xl font-bold mb-4">
      Terms of Service
    </h1>

    <p class="mb-4 text-sm text-cs-whiteish/80">
      Last updated: {{ lastUpdated }}
    </p>

    <p class="mb-4">
      These Terms of Service ("Terms") govern your use of the Circuit Scope website and PCB review service
      (collectively, the "Service"). By using the Service, you agree to these Terms. If you do not agree, you
      should not use the Service.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      1. About Circuit Scope
    </h2>
    <p class="mb-4">
      The Service is operated under the name <strong>Circuit Scope</strong>. For questions about these Terms or to
      report abuse, please
      <a
        class="underline"
        href="mailto:sara.elhark@gmail.com"
      >email us</a>.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      2. Eligibility
    </h2>
    <p class="mb-4">
      You may use the Service only if you are at least 16 years old and legally allowed to enter into these
      Terms under the laws that apply to you.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      3. Your account
    </h2>
    <p class="mb-4">
      You sign in to the Service using Google or GitHub OAuth. You are responsible for maintaining the security
      of your account and for all activity that occurs under it. If you believe your account has been compromised,
      please contact us.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      4. Public projects and comments
    </h2>
    <p class="mb-4">
      Circuit Scope is a public community for PCB design review. In general, projects and comments you post are
      public and can be viewed by anyone, including users who are not logged in. Do not post anything you would
      not want to be public.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      5. Your responsibilities and acceptable use
    </h2>
    <p class="mb-2">
      You agree that you will use the Service responsibly. In particular, you agree that you will NOT:
    </p>
    <ul class="list-disc list-inside space-y-2 mb-4">
      <li>
        Upload or share designs that you do not have the right to post, including designs that infringe
        copyright or other intellectual property rights.
      </li>
      <li>
        Upload AI-generated PCB designs where you cannot reasonably verify originality or ownership.
      </li>
      <li>
        Post spam, promotional content unrelated to PCB design, or repeated unwanted messages.
      </li>
      <li>
        Post content that is hateful, harassing, threatening, or otherwise abusive, including insults directed
        at
        individuals or groups.
      </li>
      <li>
        Post illegal content, malware, or content that is intended to damage systems or devices.
      </li>
      <li>
        Scrape, harvest, or systematically copy data from the Service, whether by bots, scripts, or other
        automated means, except as allowed by any explicit API or export functionality we provide.
      </li>
      <li>
        Attempt to circumvent security, probe for vulnerabilities, or disrupt or overload the Service.
      </li>
    </ul>
    <p class="mb-4">
      We may remove content or suspend or terminate accounts if we believe these rules are violated or if we
      are required to do so by law.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      6. Intellectual property
    </h2>
    <p class="mb-4">
      You retain any intellectual property rights you have in the designs and other content you upload to the
      Service. You are solely responsible for ensuring that you have all rights necessary to upload and share this
      content.
    </p>
    <p class="mb-4">
      By uploading content, you grant Circuit Scope a limited, non-exclusive, worldwide license to host, store,
      display, and process that content as needed to operate the Service (for example, to generate and serve
      previews, and to display your projects and comments to other users).
    </p>
    <p class="mb-4">
      Circuit Scope does not claim ownership of your designs and does not use them for purposes outside of
      providing and improving the Service.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      7. Open source software
    </h2>
    <p class="mb-4">
      Parts of the Service are built with open source software and may themselves be open source. Use of such
      software may be subject to separate open source licenses. These Terms are not intended to limit your rights
      under any applicable open source license.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      8. Service changes and availability
    </h2>
    <p class="mb-4">
      The Service is provided for free and may change over time. We may add or remove features, impose limits,
      or discontinue the Service entirely. We will try to avoid breaking changes, but we cannot guarantee
      uninterrupted or error-free operation.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      9. Disclaimers and limitation of liability
    </h2>
    <p class="mb-4">
      The Service is provided "as is" and "as available" without warranties of any kind, whether express or
      implied. To the maximum extent permitted by law, Circuit Scope disclaims all warranties, including any
      warranties of merchantability, fitness for a particular purpose, and non-infringement.
    </p>
    <p class="mb-4">
      To the extent permitted by law, Circuit Scope will not be liable for any indirect, incidental, special,
      consequential, or punitive damages, or for any loss of data, profits, or revenue, arising out of or in
      connection with your use of the Service. Our total liability for any claim relating to the Service will be
      limited to the amount you paid us for the Service in the 12 months before the claim (which is typically
      zero,
      as the Service is provided for free).
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      10. Governing law
    </h2>
    <p class="mb-4">
      These Terms are governed by the laws of Sweden, without regard to its conflict of law principles. This does
      not limit any mandatory protections you have under the laws of your country of residence.
    </p>

    <h2 class="text-xl font-semibold mt-6 mb-2">
      11. Changes to these Terms
    </h2>
    <p class="mb-4">
      We may update these Terms from time to time, for example when we change the Service or when laws change.
      When we do, we will update the "Last updated" date at the top of this page. If changes are significant, we
      may also provide additional notice within the Service. By continuing to use the Service after changes take
      effect, you agree to the updated Terms.
    </p>
  </div>
</template>

<script setup lang="ts">
const lastUpdated = 'December 2025'

defineOgImageComponent('OgTemplate', {
  heading: 'Terms of Service',
  description: 'Read the terms and conditions for using the Circuit Scope platform.',
})
</script>
