"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import {
  FiArrowUpRight,
  FiGitBranch,
  FiMaximize2,
  FiMenu,
  FiRadio,
  FiX,
} from "react-icons/fi";
import { FaPlane, FaWhatsapp } from "react-icons/fa";
import styles from "./HybridLandingPage.module.css";

const emailAddress = "aeroboundventures@gmail.com";
const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER;
const whatsappHref = whatsappNumber ? `https://wa.me/${whatsappNumber}` : "https://wa.me/";

const offerItems = [
  {
    label: "01 / Air travel",
    description: "Direct flight support with a human point of view.",
  },
  {
    label: "02 / Software development",
    description: "Web platforms and product systems built to move.",
  },
  {
    label: "03 / One connected venture",
    description: "One team connecting the journey and the machinery behind it.",
  },
];

function HybridNav() {
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className={styles.header}>
      <div className={styles.headerInner}>
        <Link href="/" className={styles.brandLink} onClick={closeMenu}>
          <span className={styles.logoFrame}>
            <Image src="/logo.png" alt="Aero Bound Ventures logo" width={40} height={40} priority />
          </span>
          <span className={styles.brandCopy}>
            <span className={styles.brandName}>Aero Bound Ventures</span>
            <span className={styles.brandTagline}>Flights + software</span>
          </span>
        </Link>

        <nav className={styles.desktopNav} aria-label="Hybrid landing navigation">
          <a href="#capabilities">Capabilities</a>
          <a href="#process">Process</a>
          <a href="#contact">Contact</a>
        </nav>

        <div className={styles.headerActions}>
          <div className={styles.bannerScope}>
            <span>Flight booking</span>
            <strong>available on /travel</strong>
          </div>
          <Link className={styles.travelLink} href="/travel">
            Explore travel
            <FiArrowUpRight aria-hidden="true" size={14} />
          </Link>
        </div>

        <button
          className={styles.menuButton}
          type="button"
          aria-expanded={menuOpen}
          aria-controls="hybrid-mobile-menu"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <FiX aria-hidden="true" size={22} /> : <FiMenu aria-hidden="true" size={22} />}
        </button>
      </div>

      <div
        id="hybrid-mobile-menu"
        className={`${styles.mobileMenu} ${menuOpen ? styles.mobileMenuOpen : ""}`}
        aria-hidden={!menuOpen}
      >
        <nav aria-label="Mobile hybrid landing navigation">
          <a href="#capabilities" onClick={closeMenu}>Capabilities</a>
          <a href="#process" onClick={closeMenu}>Process</a>
          <a href="#contact" onClick={closeMenu}>Contact</a>
          <Link href="/travel" onClick={closeMenu}>Explore travel <FiArrowUpRight aria-hidden="true" size={15} /></Link>
        </nav>
      </div>
    </header>
  );
}

function CommandCenterVisual() {
  return (
    <div className={styles.visualShell} aria-label="Flight and software command center illustration">
      <div className={styles.visualFrame} aria-hidden="true" />
      <div className={`${styles.visualFrame} ${styles.visualFrameOuter}`} aria-hidden="true" />
      <div className={styles.visualCard}>
        <div className={styles.visualHeader}>
          <div className={styles.windowTitleGroup}>
            <span className={styles.windowDots} aria-hidden="true">
              <span className={styles.dotRose} />
              <span className={styles.dotAmber} />
              <span className={styles.dotLime} />
            </span>
            <span>abv / flight + command center</span>
          </div>
          <span className={styles.liveStatus}><span /> journey live</span>
        </div>

        <div className={styles.plotArea}>
          <span className={`${styles.nodeDot} ${styles.nodeOne}`} aria-hidden="true" />
          <span className={`${styles.nodeDot} ${styles.nodeTwo}`} aria-hidden="true" />
          <span className={`${styles.nodeDot} ${styles.nodeThree}`} aria-hidden="true" />
          <svg className={styles.routeSvg} viewBox="0 0 620 420" preserveAspectRatio="none" aria-hidden="true">
            <path className={styles.routeGlow} d="M105 90 C190 40 215 190 295 178 C375 165 390 285 480 208" />
            <path className={styles.routePath} d="M105 90 C190 40 215 190 295 178 C375 165 390 285 480 208" />
            <path className={styles.routeBranches} d="M105 90 L105 370 M295 178 L295 370 M480 208 L480 370" />
          </svg>

          <div className={`${styles.floatingCard} ${styles.signalCard}`}>
            <div className={styles.cardMeta}><span>flight signal / 01</span><FiRadio aria-hidden="true" size={15} /></div>
            <strong>0.94 <em>σ</em></strong>
            <span className={styles.cardStatus}>booking route locked</span>
          </div>

          <div className={`${styles.floatingCard} ${styles.opsCard}`}>
            <div className={styles.cardMeta}><span>travel ops</span><strong>99.98%</strong></div>
            <div className={styles.metricList}>
              <span><i>booking_route</i><b>ready</b></span>
              <span><i>journey_status</i><b className={styles.limeText}>moving</b></span>
              <span><i>handoff</i><b className={styles.blueText}>clear</b></span>
            </div>
          </div>

          <span className={styles.mapCaption}>route map / journeys + systems</span>
        </div>

        <div className={styles.visualMetrics}>
          <div><span>routes supported</span><strong>2.4 <em>×</em></strong></div>
          <div><span>open loops</span><strong>03</strong></div>
          <div><span>next departure</span><strong className={styles.limeText}>Now</strong></div>
        </div>
      </div>
    </div>
  );
}

function OfferStrip() {
  return (
    <section className={styles.offerSection} aria-label="Aero Bound Ventures services">
      <div className={styles.offerGrid}>
        {offerItems.map((item) => (
          <div className={styles.offerItem} key={item.label}>
            <span>{item.label}</span>
            <p>{item.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function CapabilitiesSection() {
  return (
    <section id="capabilities" className={`${styles.section} ${styles.gridSection}`}>
      <div className={styles.capabilitiesLayout}>
        <div className={styles.sectionIntro}>
          <span className={styles.eyebrow}>Capabilities / 03 coordinates</span>
          <h2>From air travel to shipped system.</h2>
          <p>We connect human flight support with software development — one useful decision at a time.</p>
          <span className={styles.sectionRule}><i /> one team, end to end</span>
        </div>

        <div className={styles.capabilityGrid}>
          <article className={`${styles.capabilityCard} ${styles.featuredCard}`}>
            <div className={styles.cardDecoration} aria-hidden="true"><span /><span /><i /></div>
            <div className={styles.capabilityCopy}>
              <span className={styles.cardIndex}>01 / JOURNEY</span>
              <h3>Travel experiences with a point of view.</h3>
              <p>We make flight support clear and personal: from direct booking guidance to the moments that make a journey feel easy.</p>
              <div className={styles.tagRow}><span>flight support</span><span>booking flow</span><span>journey care</span></div>
            </div>
          </article>

          <article className={styles.capabilityCard}>
            <div className={styles.cardHeader}><span className={styles.blueText}>02 / BUILD</span><FiMaximize2 aria-hidden="true" size={16} /></div>
            <h3>Web platforms for the way people move.</h3>
            <p>Fast, expressive digital products for travel teams and growing businesses.</p>
            <div className={styles.codeBlock}>
              <span className={styles.codeDots}><i /><i /><i /></span>
              <code>const <b>journey</b> = <em>clarity</em> + <strong>care</strong>;</code>
              <small>// ready for departure</small>
            </div>
          </article>

          <article className={styles.capabilityCard}>
            <div className={styles.cardHeader}><span className={styles.limeText}>03 / ORCHESTRATE</span><FiGitBranch aria-hidden="true" size={17} /></div>
            <h3>Operations that keep journeys moving.</h3>
            <p>Automation and internal tools that protect momentum from first brief to final handoff.</p>
            <div className={styles.statusTracker}>
              <span><i className={styles.limeDot} /> booking <b>routed</b></span>
              <span><i className={styles.cyanDot} /> decision <b className={styles.cyanText}>human</b></span>
              <span><i className={styles.blueDot} /> handoff <b className={styles.blueText}>clear</b></span>
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}

function ProcessSection() {
  const steps = [
    ["01", "Frame the journey", "What is true, useful, and worth changing?"],
    ["02", "Map the system", "Make the experience and architecture legible."],
    ["03", "Build the loop", "Ship the smallest version that can move us."],
    ["04", "Keep it moving", "Tune, support, and leave the team stronger."],
  ];

  return (
    <section id="process" className={`${styles.processSection} ${styles.section}`}>
      <div className={styles.processHeader}>
        <div><span className={styles.eyebrow}>Process / route map</span><h2>A clear route from brief to boarding.</h2></div>
        <p>No black boxes. No handoffs into the void. Just a visible path from the first question to the working journey or system.</p>
      </div>
      <div className={styles.processGrid}>
        <div className={styles.processLine} aria-hidden="true" />
        {steps.map(([number, title, description]) => (
          <div className={styles.processStep} key={number}>
            <span className={styles.stepNumber}>{number}</span>
            <h3>{title}</h3>
            <p>{description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function PositionSection() {
  return (
    <section className={`${styles.positionSection} ${styles.section}`}>
      <div className={styles.positionLayout}>
        <div className={styles.positionHeading}>
          <span className={styles.eyebrow}>Mission + vision / direction</span>
          <h2>What drives us. Where we’re going.</h2>
        </div>
        <div className={styles.missionVisionGrid}>
          <article className={`${styles.directionCard} ${styles.missionCard}`}>
            <span className={styles.directionIndex}>01 / NOW</span>
            <h3>Mission</h3>
            <p>To simplify air travel and build software that moves people and businesses forward.</p>
          </article>
          <article className={`${styles.directionCard} ${styles.visionCard}`}>
            <span className={styles.directionIndex}>02 / NEXT</span>
            <h3>Vision</h3>
            <p>To connect people and opportunities through travel and technology.</p>
          </article>
        </div>
      </div>
    </section>
  );
}

function ContactSection() {
  return (
    <section id="contact" className={styles.contactSection}>
      <div className={styles.contactCard}>
        <div>
          <span className={styles.eyebrow}>Contact / open channel</span>
          <h2>Have a journey or system in mind? Let’s give it a route.</h2>
          <p>No forms, no funnels. Send a note about a flight, a travel need, or a software system you want to move.</p>
          <div className={styles.contactLinks}>
            <a href={`mailto:${emailAddress}`}>{emailAddress}</a>
            <a href={whatsappHref} target="_blank" rel="noopener noreferrer"><FaWhatsapp aria-hidden="true" size={16} /> WhatsApp the team</a>
          </div>
        </div>
        <a className={styles.threadButton} href={`mailto:${emailAddress}`}>Start the thread <FiArrowUpRight aria-hidden="true" size={16} /></a>
      </div>
    </section>
  );
}

function HybridFooter() {
  return (
    <footer className={styles.footer}>
      <div className={styles.footerInner}>
        <div className={styles.footerIdentity}>
          <span className={styles.footerLogo}><Image src="/logo.png" alt="Aero Bound Ventures logo" width={28} height={28} /></span>
          <span>© {new Date().getFullYear()} Aero Bound Ventures / Travel + software</span>
        </div>
        <Link href="/travel">Visit the travel experience <FiArrowUpRight aria-hidden="true" size={14} /></Link>
      </div>
    </footer>
  );
}

export default function HybridLandingPage() {
  return (
    <div className={styles.page}>
      <HybridNav />
      <main id="top">
        <section className={`${styles.hero} ${styles.gridSection}`}>
          <div className={styles.noiseLayer} aria-hidden="true" />
          <div className={`${styles.heroRing} ${styles.heroRingLarge}`} aria-hidden="true" />
          <div className={`${styles.heroRing} ${styles.heroRingSmall}`} aria-hidden="true" />
          <div className={styles.heroLayout}>
            <div className={styles.heroCopy}>
              <span className={styles.heroBadge}><i /> Air travel + software development</span>
              <h1>Air travel and software for journeys that keep moving.</h1>
              <p>Aero Bound Ventures is an air travel company and software development studio — pairing direct flight support with digital products and intelligent operations.</p>
              <div className={styles.heroActions}>
                <a className={styles.primaryButton} href="#contact">Start a conversation <FiArrowUpRight aria-hidden="true" size={16} /></a>
                <Link className={styles.secondaryButton} href="/travel">Book flights &amp; travel <FaPlane aria-hidden="true" size={17} /></Link>
              </div>
              <div className={styles.heroMeta}>
                <span><i className={styles.limeDot} /> Flight operations + product systems</span>
                <span><i className={styles.cyanDot} /> Human-led service</span>
              </div>
            </div>
            <CommandCenterVisual />
          </div>
        </section>
        <OfferStrip />
        <CapabilitiesSection />
        <ProcessSection />
        <PositionSection />
        <ContactSection />
      </main>
      <HybridFooter />
    </div>
  );
}
