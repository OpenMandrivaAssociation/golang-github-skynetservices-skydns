%if 0%{?fedora} || 0%{?rhel} == 6
%global with_devel 1
%global with_bundled 0
%global with_debug 1
# server test takes more them 4 minutes, skipping
%global with_check 0
%global with_unit_test 1
%else
%global with_devel 0
%global with_bundled 0
%global with_debug 0
%global with_check 0
%global with_unit_test 0
%endif

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%define copying() \
%if 0%{?fedora} >= 21 || 0%{?rhel} >= 7 \
%license %{*} \
%else \
%doc %{*} \
%endif

%global isgccgoarch 0
%if 0%{?gccgo_arches:1}
%ifarch %{gccgo_arches}
%global isgccgoarch 1
%endif
%endif

%global provider        github
%global provider_tld    com
%global project         skynetservices
%global repo            skydns
# https://github.com/skynetservices/skydns
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          8688008ce43981615bad361523f68f1b36af2595
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:           golang-%{provider}-%{project}-%{repo}
Version:        2.5.3
Release:        0.1.a.git%{shortcommit}%{?dist}
Summary:        DNS service discovery for etcd
License:        MIT
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz
Source1:        %{repo}.service
Source2:        %{repo}.conf
Source3:        %{repo}.socket

# If go_arches not defined fall through to implicit golang archs
%if 0%{?go_arches:1}
ExclusiveArch:  %{go_arches}
%else
ExclusiveArch:   %{ix86} x86_64 %{arm}
%endif
# If gccgo_arches does not fit or is not defined fall through to golang
%if %{isgccgoarch}
BuildRequires:   gcc-go >= %{gccgo_min_vers}
%else
BuildRequires:   golang
%endif

%description
%{summary}

%package -n %{repo}
Summary:        %{summary}

BuildRequires:  systemd
%if ! 0%{?with_bundled}
BuildRequires:  golang(github.com/coreos/go-etcd/etcd)
BuildRequires:  golang(github.com/coreos/go-systemd/activation)
BuildRequires:  golang(github.com/miekg/dns)
BuildRequires:  golang(github.com/prometheus/client_golang/prometheus)
BuildRequires:  golang(github.com/rcrowley/go-metrics)
BuildRequires:  golang(github.com/rcrowley/go-metrics/stathat)
%endif

Requires:         etcd
Requires(pre):    shadow-utils
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd

Provides: %{repo} = %{version}-%{release}

%description -n %{repo}
%{summary}

%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch

%if 0%{?with_check}
BuildRequires: golang(github.com/coreos/go-etcd/etcd)
BuildRequires: golang(github.com/coreos/go-systemd/activation)
BuildRequires: golang(github.com/miekg/dns)
BuildRequires: golang(github.com/prometheus/client_golang/prometheus)
BuildRequires: golang(github.com/rcrowley/go-metrics)
BuildRequires: golang(github.com/rcrowley/go-metrics/stathat)
%endif

Requires:      golang(github.com/coreos/go-etcd/etcd)
Requires:      golang(github.com/coreos/go-systemd/activation)
Requires:      golang(github.com/miekg/dns)
Requires:      golang(github.com/prometheus/client_golang/prometheus)
Requires:      golang(github.com/rcrowley/go-metrics)
Requires:      golang(github.com/rcrowley/go-metrics/stathat)

Provides:      golang(%{import_path}/backends/etcd) = %{version}-%{release}
Provides:      golang(%{import_path}/cache) = %{version}-%{release}
Provides:      golang(%{import_path}/msg) = %{version}-%{release}
Provides:      golang(%{import_path}/server) = %{version}-%{release}
Provides:      golang(%{import_path}/stats) = %{version}-%{release}

%description devel
%{summary}

This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test}
%package unit-test
Summary:         Unit tests for %{name} package
# If go_arches not defined fall through to implicit golang archs
%if 0%{?go_arches:1}
ExclusiveArch:  %{go_arches}
%else
ExclusiveArch:   %{ix86} x86_64 %{arm}
%endif
# If gccgo_arches does not fit or is not defined fall through to golang
%if %{isgccgoarch}
BuildRequires:   gcc-go >= %{gccgo_min_vers}
%else
BuildRequires:   golang
%endif

%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%description unit-test
%{summary}

This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%setup -q -n %{repo}-%{commit}

%build
# If gccgo_arches does not fit or is not defined fall through to golang
# gccco arches
%if %{isgccgoarch}
%if 0%{?gcc_go_build:1}
export GOCOMPILER='%{gcc_go_build}'
%else
echo "No compiler for SA"
exit 1
%endif
# golang arches (due to ExclusiveArch)
%else
%if 0%{?golang_build:1}
export GOCOMPILER='%{golang_build} -ldflags "$LDFLAGS"'
%else
export GOCOMPILER='go build -ldflags "$LDFLAGS"'
%endif
%endif

export LDFLAGS=
%if 0%{?with_debug}
%if %{isgccgoarch}
export OLD_RPM_OPT_FLAGS="$RPM_OPT_FLAGS"
function gobuild {
export RPM_OPT_FLAGS="$OLD_RPM_OPT_FLAGS -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \n')"
eval ${GOCOMPILER} -a -v -x "$@";
}
%else
export OLD_LDFLAGS="$LDFLAGS"
function gobuild {
export LDFLAGS="$OLD_LDFLAGS -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \n')"
eval ${GOCOMPILER} -a -v -x "$@";
}
%endif
%else
function gobuild { eval ${GOCOMPILER} -a -v -x "$@"; }
%endif

mkdir -p src/github.com/skynetservices
ln -s ../../../ src/github.com/skynetservices/skydns

%if ! 0%{?with_bundled}
export GOPATH=$(pwd):%{gopath}
%else
echo "Unable to build from bundled dependencies. No Godeps directory"
exit 1
%endif

gobuild -o bin/%{repo} %{import_path}

%install
install -d -p %{buildroot}%{_bindir}
install -p -m 755 bin/%{repo} %{buildroot}%{_bindir}
install -D -p -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{repo}.service
install -d -m 0755 %{buildroot}%{_sysconfdir}/%{repo}
install -m 644 -t %{buildroot}%{_sysconfdir}/%{repo} %{SOURCE2}
install -D -p -m 0644 %{SOURCE3} %{buildroot}%{_unitdir}/%{repo}.socket


# And create /var/lib/skydns, even if not used at the moment
install -d -m 0755 %{buildroot}%{_sharedstatedir}/%{repo}

# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . -iname "*.go" \! -iname "*_test.go") ; do
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list
done
%endif

# testing files for this project
%if 0%{?with_unit_test}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test.file-list
for file in $(find . -iname "*_test.go"); do
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test.file-list
done
%endif

%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%if %{isgccgoarch}
function gotest { %{gcc_go_test} "$@"; }
%else
%if 0%{?golang_test:1}
function gotest { %{golang_test} "$@"; }
%else
function gotest { go test "$@"; }
%endif
%endif

export GOPATH=%{buildroot}/%{gopath}:%{gopath}
gotest %{import_path}/cache
gotest %{import_path}/msg
gotest %{import_path}/server
%endif

%pre -n %{repo}
getent group %{repo} >/dev/null || groupadd -r %{repo}
getent passwd %{repo} >/dev/null || useradd -r -g %{repo} -d %{_sharedstatedir}/%{repo} \
        -s /sbin/nologin -c "skydns user" %{repo}

%post -n %{repo}
%systemd_post %{repo}.service

%preun -n %{repo}
%systemd_preun %{repo}.service

%postun -n %{repo}
%systemd_postun %{repo}.service

%files -n %{repo}
%copying LICENSE
%doc README.md AUTHORS CONTRIBUTORS
%{_bindir}/%{repo}
%dir %attr(-,%{repo},%{repo}) %{_sharedstatedir}/%{repo}
%{_unitdir}/%{repo}.service
%{_unitdir}/%{repo}.socket
%config(noreplace) %{_sysconfdir}/%{repo}

%if 0%{?with_devel}
%files devel -f devel.file-list
%copying LICENSE
%doc README.md AUTHORS CONTRIBUTORS
%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}
%dir %{gopath}/src/%{import_path}
%endif

%if 0%{?with_unit_test}
%files unit-test -f unit-test.file-list
%copying LICENSE
%doc README.md AUTHORS CONTRIBUTORS
%endif

%changelog
* Tue Oct 27 2015 jchaloup <jchaloup@redhat.com> - 2.5.3-0.1.a.git8688008
- Update to 2.5.3.a
  related: #1269191

* Wed Oct 21 2015 jchaloup <jchaloup@redhat.com> - 0-0.8.git6c94cbe
- Introduce skydns.docker to be able to bind to port 53 as a skydns user
  resolves: #1269191

* Mon Aug 24 2015 jchaloup <jchaloup@redhat.com> - 0-0.7.git6c94cbe
- Update spec file to spec-2.0
  resolves: #1250508

* Mon Jun 22 2015 jchaloup <jchaloup@redhat.com> - 0-0.6.git6c94cbe
- Update pre, post, preun, postun sections to belong to skydns subpackage
  related: #1181197

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0-0.5.git6c94cbe
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed Jun 03 2015 jchaloup <jchaloup@redhat.com> - 0-0.4.git6c94cbe
- Bump to upstream 6c94cbe92349cf550e64752a7cb72c98bcc44325
- Add skydns subpackage with skydns binary
- Add debuginfo
- Move LICENSE under license macro
- Add skydns.service and skydns.conf files
  related: #1181197

* Mon Jan 19 2015 jchaloup <jchaloup@redhat.com> - 0-0.3.git245a121
- Requires on kubernetes makes building of kubernetes failing.
  related: #1181197

* Sun Jan 18 2015 jchaloup <jchaloup@redhat.com> - 0-0.2.git245a121
- Fix Requires on kubernetes
  related: #1181197

* Mon Jan 12 2015 jchaloup <jchaloup@redhat.com> - 0-0.1.git245a121
- First package for Fedora
  resolves: #1181197
