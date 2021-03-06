# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
%define etc_flume /etc/flume-ng/conf
%define bin_flume %{_bindir}
%define man_flume %{_mandir}
%define lib_flume /usr/lib/flume-ng
%define log_flume /var/log/flume-ng
%define run_flume /var/run/flume-ng

%if  %{?suse_version:1}0

# Only tested on openSUSE 11.4. le'ts update it for previous release when confirmed
%if 0%{suse_version} > 1130
%define suse_check \# Define an empty suse_check for compatibility with older sles
%endif

# SLES is more strict and check all symlinks point to valid path
# But we do point to a hadoop jar which is not there at build time
# (but would be at install time).
# Since our package build system does not handle dependencies,
# these symlink checks are deactivated
%define __os_install_post \
    %{suse_check} ; \
    /usr/lib/rpm/brp-compress ; \
    %{nil}

%define doc_flume %{_docdir}/flume-ng
%define alternatives_cmd update-alternatives
%global initd_dir %{_sysconfdir}/rc.d

%else

%define doc_flume %{_docdir}/flume-ng-%{flume_ng_version}
%define alternatives_cmd alternatives
%global initd_dir %{_sysconfdir}/rc.d/init.d

%endif



Name: flume-ng
Version: %{flume_ng_version}
Release: %{flume_ng_release}
Summary:  Flume is a reliable, scalable, and manageable distributed log collection application for collecting data such as logs and delivering it to data stores such as Hadoop's HDFS.
URL: http://incubator.apache.org/projects/flume.html
Group: Development/Libraries
Buildroot: %{_topdir}/INSTALL/%{name}-%{version}
BuildArch: noarch
License: APL2
Source0: %{name}-%{flume_ng_patched_version}.tar.gz
Source1: do-component-build
Source2: install_%{name}.sh
Source3: %{name}-agent.init
Source4: flume-ng-agent.default
Requires: /usr/sbin/useradd
Requires: coreutils
Requires: hadoop-hdfs
Requires: bigtop-utils

%if  0%{?mgaversion}
Requires: bsh-utils
%else
Requires: sh-utils
%endif

%description 
Flume is a reliable, scalable, and manageable distributed data collection application for collecting data such as logs and delivering it to data stores such as Hadoop's HDFS.  It can efficiently collect, aggregate, and move large amounts of log data.  It has a simple, but flexible, architecture based on streaming data flows.  It is robust and fault tolerant with tunable reliability mechanisms and many failover and recovery mechanisms.  The system is centrally managed and allows for intelligent dynamic management. It uses a simple extensible data model that allows for online analytic applications.

%package agent
Summary: The flume agent daemon is a core element of flume's data path and is responsible for generating, processing, and delivering data.
Group: Development/Libraries
BuildArch: noarch
Requires: %{name} = %{version}-%{release}
Requires: /sbin/service
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig

%if  %{?suse_version:1}0
# Required for init scripts
Requires: insserv
%endif

%if  0%{?mgaversion}
# Required for init scripts
Requires: initscripts
%endif

# CentOS 5 does not have any dist macro
# So I will suppose anything that is not Mageia or a SUSE will be a RHEL/CentOS/Fedora
%if %{!?suse_version:1}0 && %{!?mgaversion:1}0
# Required for init scripts
Requires: redhat-lsb
%endif

%description agent
Flume is a reliable, scalable, and manageable distributed data collection application for collecting data such as logs and delivering it to data stores such as Hadoop's HDFS.  It can efficiently collect, aggregate, and move large amounts of log data.  It has a simple, but flexible, architecture based on streaming data flows.  It is robust and fault tolerant with tunable reliability mechanisms and many failover and recovery mechanisms.  The system is centrally managed and allows for intelligent dynamic management. It uses a simple extensible data model that allows for online analytic applications.


%package doc
Summary: Flume NG Documentation
Group: Documentation
BuildArch: noarch

%description doc
Documentation for Flume NG


%prep
%setup -n flume-%{flume_ng_patched_version}

%build
env FULL_VERSION=%{flume_ng_patched_version} sh %{SOURCE1}

%install
%__rm -rf $RPM_BUILD_ROOT
sh %{SOURCE2} \
          --build-dir=$PWD \
          --prefix=$RPM_BUILD_ROOT \
	  --doc-dir=%{doc_flume}
%__install -d -m 0755 $RPM_BUILD_ROOT/%{initd_dir}/


# Install init script
init_file=$RPM_BUILD_ROOT/%{initd_dir}/%{name}-agent
%__cp %{SOURCE3} $init_file
chmod 755 $init_file


%__install -d -m 0755 $RPM_BUILD_ROOT/usr/bin

%__install -d -m 0755 $RPM_BUILD_ROOT/etc/default
%__cp %{SOURCE4} $RPM_BUILD_ROOT/etc/default/%{name}-agent


%pre
getent group flume >/dev/null || groupadd -r flume
getent passwd flume >/dev/null || useradd -c "Flume" -s /sbin/nologin -g flume -r -d %{run_flume} flume 2> /dev/null || :
%__install -d -o flume -g flume -m 0755 /var/log/flume-ng

# Manage configuration symlink
%post
%{alternatives_cmd} --install %{etc_flume} %{name}-conf %{etc_flume}.empty 30

%preun
if [ "$1" = 0 ]; then
        %{alternatives_cmd} --remove %{name}-conf %{etc_flume}.empty || :
fi

%post agent
chkconfig --add %{name}-agent

%preun agent
if [ $1 = 0 ] ; then
        service %{name}-agent stop > /dev/null 2>&1
        chkconfig --del %{name}-agent
fi
%postun agent
if [ $1 -ge 1 ]; then
        service %{name}-agent condrestart >/dev/null 2>&1
fi


%files 
%defattr(644,root,root,755)

%dir %{etc_flume}.empty
%dir %{lib_flume}
%dir %{lib_flume}/bin
%dir %{lib_flume}/lib
%dir %{lib_flume}/cloudera

%config(noreplace) %{etc_flume}.empty/*
%attr(0755,root,root) %{bin_flume}/flume-ng
%attr(0755,root,root) %{lib_flume}/bin/flume-ng
%{lib_flume}/cloudera/cdh_version.properties
%{lib_flume}/lib/*.jar
%{lib_flume}/conf

%files agent
%attr(0755,root,root)/%{initd_dir}/%{name}-agent
%attr(0644,root,root) %config(noreplace) /etc/default/%{name}-agent

%files doc
%defattr(644,root,root,755)
%doc %{doc_flume}/

